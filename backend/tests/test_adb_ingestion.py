"""Isolated synthetic SDMX fixtures, not application data."""

import asyncio
import csv
import io

import httpx
import pytest
from sqlalchemy import func, select

from backend.app.models import (
    Country,
    DataSnapshot,
    Indicator,
    IngestionRun,
    Observation,
)
from ingestion.connectors.adb import (
    AdbClient,
    ECONOMY_CODES,
    SERIES,
    make_indicator,
    read_country_codes,
)
from ingestion.connectors.adb_rows import parse_rows
from ingestion.connectors.http import SourceError, SourceHTTP
from ingestion.pipelines.additional_sources import ingest_source

FIELDS = [
    "DATAFLOW",
    "FREQ",
    "INDICATOR",
    "ECONOMY_CODE",
    "TIME_PERIOD",
    "OBS_VALUE",
    "UNIT",
    "UNIT_MULT",
    "OBS_STATUS",
    "REF_YEAR",
    "DATA_SOURCE",
    "FOOTNOTE",
]


def csv_response(rows):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def synthetic_rows(flow, countries=("IND", "JPN")):
    rows = []
    for code, dataflow in SERIES.items():
        if dataflow != flow:
            continue
        for country in countries:
            if flow == "DF_EXT_DEBT" and country == "JPN":
                continue  # An unavailable series is an explicit gap.
            for year in (2023, 2024):
                rows.append(
                    {
                        "DATAFLOW": f"ADB:{flow}(1.0)",
                        "FREQ": "A",
                        "INDICATOR": code,
                        "ECONOMY_CODE": country,
                        "TIME_PERIOD": str(year),
                        "OBS_VALUE": "0" if year == 2023 else "2",
                        "UNIT": "USD",
                        "UNIT_MULT": "6",
                        "OBS_STATUS": "A",
                        "REF_YEAR": "Synthetic reference year",
                        "DATA_SOURCE": "Synthetic source",
                        "FOOTNOTE": "Synthetic footnote, with comma",
                    }
                )
    return rows


def adb_response(request, problem=None, reverse=False):
    path = request.url.path
    if "codelist" in path:
        return httpx.Response(
            200,
            text='<s:Codelist xmlns:s="urn:test"><s:Code id="IND"/><s:Code id="JPN"/><s:Code id="PHI"/><s:Code id="IND_10"/></s:Codelist>',
        )
    if "indicators" in path:
        flow = path.split("/")[-1]
        return httpx.Response(
            200,
            json=[
                {
                    "code": code,
                    "name": f"Synthetic {code}",
                    "description": "Synthetic definition",
                }
                for code, dataflow in SERIES.items()
                if dataflow == flow
            ],
        )
    flow = path.split("/")[-2].split(",")[1]
    rows = synthetic_rows(flow)
    if problem == "unit":
        rows[0]["UNIT"] = "JPY"
    if problem == "scale":
        rows[0]["UNIT_MULT"] = "bad"
    if problem == "value":
        rows[0]["OBS_VALUE"] = "NaN"
    if problem == "forecast":
        rows[0]["OBS_STATUS"] = "F"
    if problem == "country":
        rows[0]["ECONOMY_CODE"] = "CHN"
    if problem == "year":
        rows[0]["TIME_PERIOD"] = "2030"
    if problem == "duplicate":
        rows.append(dict(rows[0]))
    if problem == "flow":
        rows[0]["DATAFLOW"] = "ADB:OTHER(1.0)"
    if reverse:
        rows.reverse()
    return httpx.Response(200, text=csv_response(rows))


def import_adb(db, tmp_path, problem=None, reverse=False, countries=None):
    async def run():
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: adb_response(request, problem, reverse)
            )
        ) as client:
            return await ingest_source(
                db,
                AdbClient(client, retries=0, interval=0),
                countries or ["IND", "JPN"],
                2023,
                2024,
                tmp_path,
            )

    return asyncio.run(run())


@pytest.fixture
def adb_db(populated):
    populated.add(
        Country(iso3="JPN", name="Synthetic Japan", region="Test", income_group="Test")
    )
    populated.commit()
    return populated


def test_adb_sources_units_metadata_and_missing_series(adb_db, tmp_path, client):
    result = import_adb(adb_db, tmp_path)
    assert result.records_processed == 8
    assert adb_db.scalar(select(func.count()).select_from(Observation)) == 32
    snapshot = adb_db.get(DataSnapshot, result.dataset_version)
    assert (
        snapshot.manifest["provider_metadata"]["rows"][0]["DATA_SOURCE"]
        == "Synthetic source"
    )
    assert (
        snapshot.manifest["provider_metadata"]["rows"][0]["FOOTNOTE"]
        == "Synthetic footnote, with comma"
    )
    assert all(
        row.unit == "million US$"
        for row in adb_db.scalars(select(Indicator).where(Indicator.code.like("ADB.%")))
    )
    data = client.get("/api/data/map?indicator=ADB.DF_IL.RAFA_USD_TOT&year=2023").json()
    assert data["source_name"] == "Asian Development Bank KIDB"
    assert next(row for row in data["countries"] if row["iso3"] == "IND")["value"] == 0
    debt = client.get(
        "/api/countries/JPN/indicators?indicator=ADB.DF_EXT_DEBT.DT_INT_DLXF_CD"
    ).json()
    assert debt["items"] == []


def test_adb_repeat_is_idempotent_even_if_row_order_changes(adb_db, tmp_path):
    first = import_adb(adb_db, tmp_path)
    assert (
        import_adb(adb_db, tmp_path, reverse=True).dataset_version
        == first.dataset_version
    )
    assert adb_db.scalar(select(func.count()).select_from(Observation)) == 32


@pytest.mark.parametrize(
    "problem",
    ["unit", "scale", "value", "forecast", "country", "year", "duplicate", "flow"],
)
def test_adb_bad_response_is_atomic_and_audited(adb_db, tmp_path, problem):
    with pytest.raises((SourceError, ValueError)):
        import_adb(adb_db, tmp_path, problem)
    assert adb_db.scalar(select(func.count()).select_from(Observation)) == 24
    assert (
        adb_db.scalar(select(IngestionRun).where(IngestionRun.status == "failed"))
        is not None
    )


def test_adb_rejects_countries_outside_its_coverage(populated, tmp_path):
    with pytest.raises(SourceError, match="does not cover USA"):
        import_adb(populated, tmp_path, countries=["USA"])


def test_adb_explicit_country_alias_and_subnational_exclusion():
    assert ECONOMY_CODES["PHL"] == "PHI"
    assert read_country_codes(
        '<s:List xmlns:s="urn:test"><s:Code id="PHI"/><s:Code id="PHI_10"/></s:List>'
    ) == {"PHI"}
    row = synthetic_rows("DF_IL", countries=["PHI"])[0]
    observations, _ = parse_rows(
        csv_response([row]), "DF_IL", ["RAFA_USD_TOT"], {"PHI": "PHL"}, 2023, 2024
    )
    assert observations[0]["country_iso3"] == "PHL"


def test_adb_currency_scales_and_explicit_null():
    rows = synthetic_rows("DF_IL", countries=["IND"])
    rows[0].update(OBS_VALUE="2500000", UNIT_MULT="0")
    rows[1].update(OBS_VALUE="", OBS_STATUS="M")
    observations, _ = parse_rows(
        csv_response(rows), "DF_IL", ["RAFA_USD_TOT"], {"IND": "IND"}, 2023, 2024
    )
    assert [row["value"] for row in observations] == [2.5, None]
    assert all(row["source_revision_date"] is None for row in observations)


def test_adb_missing_description_is_disclosed_and_missing_name_fails():
    definition = {
        "code": "DT_AMT_DLXF_CD",
        "name": "Synthetic principal",
        "description": None,
    }
    indicator = make_indicator("DT_AMT_DLXF_CD", "DF_EXT_DEBT", [definition])
    assert "not supplied a detailed definition" in indicator["definition"]
    definition["name"] = None
    with pytest.raises(SourceError, match="omitted the definition"):
        make_indicator("DT_AMT_DLXF_CD", "DF_EXT_DEBT", [definition])


def test_source_http_paces_consecutive_requests(monkeypatch):
    delays = []

    async def track_sleep(delay):
        delays.append(delay)

    monkeypatch.setattr("ingestion.connectors.http.time.monotonic", lambda: 100)
    monkeypatch.setattr("ingestion.connectors.http.asyncio.sleep", track_sleep)

    async def run():
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(200))
        ) as client:
            source = SourceHTTP(client, "https://example.test", interval=3.1)
            await source.get("first")
            await source.get("second")

    asyncio.run(run())
    assert delays == [3.1]
