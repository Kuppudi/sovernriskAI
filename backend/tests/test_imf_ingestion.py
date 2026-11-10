"""Synthetic fixtures only: these values never enter the application's database."""

import asyncio
import json

import httpx
import pytest
from sqlalchemy import func, select

from backend.app.models import (
    Country,
    DataSnapshot,
    DataSource,
    Indicator,
    IngestionRun,
    Observation,
)
from ingestion.connectors.http import SourceError, SourceHTTP
from ingestion.connectors.imf import ImfClient, SERIES
from ingestion.pipelines.additional_sources import ingest_source


def imf_response(request, problem=None, changed=False):
    if request.url.path.endswith("countries"):
        return httpx.Response(200, json={"countries": {"USA": {}, "IND": {}}})
    code = request.url.path.split("/")[-3]
    dataset, unit = SERIES[code]
    metadata = {
        "label": f"Synthetic {code}",
        "description": "Synthetic definition",
        "source": "Synthetic release",
        "dataset": dataset,
        "unit": unit,
        "projection-year": 2025,
        "last-modified": "2025-03-01 00:00:00",
    }
    series = {
        country: {"2023": 0, "2024": 2.5, "2025": 99}
        for country in ("USA", "IND", "CHN")
    }
    if code == "GGXWDG_NGDP":
        series["USA"]["2024"] = 3 if changed else None
    if problem == "unit":
        metadata["unit"] = "US dollars"
    if problem == "dataset":
        metadata["dataset"] = "OTHER"
    if problem == "cutoff":
        metadata["projection-year"] = 2024
    if problem == "missing_cutoff":
        metadata.pop("projection-year")
    if problem == "invalid_value":
        series["IND"]["2023"] = "not numeric"
    if problem == "no_data":
        series["IND"] = {}
    if problem == "missing_year":
        series["IND"].pop("2023")
    return httpx.Response(
        200, json={"indicators": {code: metadata}, "values": {code: series}}
    )


def import_imf(db, tmp_path, problem=None, changed=False):
    async def run():
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: imf_response(request, problem, changed)
            )
        ) as client:
            return await ingest_source(
                db, ImfClient(client, retries=0), ["USA", "IND"], 2023, 2024, tmp_path
            )

    return asyncio.run(run())


def test_imf_preserves_sources_units_nulls_and_only_requested_history(
    populated, tmp_path, client
):
    country_name = populated.get(Country, "IND").name
    result = import_imf(populated, tmp_path)
    assert result.records_processed == 16
    assert populated.scalar(select(func.count()).select_from(Observation)) == 40
    assert populated.get(Country, "IND").name == country_name
    snapshot = populated.get(DataSnapshot, result.dataset_version)
    assert (
        snapshot.manifest["provider_metadata"]["IMF.WEO.GGXWDG_NGDP"]["projection-year"]
        == 2025
    )
    assert len(json.loads(open(snapshot.raw_path).read())["pages"]) == 5
    definitions = populated.scalars(
        select(Indicator).where(Indicator.code.like("IMF.%"))
    ).all()
    assert len(definitions) == 4
    assert all(row.unit == "% of GDP" for row in definitions)
    assert (
        populated.get(DataSource, definitions[0].source_id).provider_name
        == "IMF DataMapper"
    )
    rows = client.get(
        "/api/countries/USA/indicators?indicator=IMF.WEO.GGXWDG_NGDP&start_year=2023&end_year=2024"
    ).json()["items"]
    assert [row["value"] for row in rows] == [0, None]
    assert all(row["source"] == "IMF DataMapper" for row in rows)
    map_data = client.get(
        "/api/data/map?indicator=IMF.WEO.GGXWDG_NGDP&year=2024"
    ).json()
    assert map_data["source_name"] == "IMF DataMapper"


def test_imf_repeat_and_revision_preserve_immutable_history(populated, tmp_path):
    first = import_imf(populated, tmp_path)
    version = first.dataset_version
    assert import_imf(populated, tmp_path).dataset_version == version
    assert populated.scalar(select(func.count()).select_from(Observation)) == 40
    assert import_imf(populated, tmp_path, changed=True).dataset_version != version
    assert populated.scalar(select(func.count()).select_from(Observation)) == 56
    assert (
        populated.scalar(
            select(func.count())
            .select_from(Observation)
            .where(Observation.dataset_version == version)
        )
        == 16
    )


@pytest.mark.parametrize(
    "problem",
    ["unit", "dataset", "cutoff", "missing_cutoff", "invalid_value", "no_data"],
)
def test_imf_failed_import_is_atomic_and_audited(populated, tmp_path, problem):
    with pytest.raises((SourceError, ValueError)):
        import_imf(populated, tmp_path, problem)
    assert populated.scalar(select(func.count()).select_from(Observation)) == 24
    assert (
        populated.scalar(select(IngestionRun).where(IngestionRun.status == "failed"))
        is not None
    )
    assert populated.scalar(select(func.count()).select_from(Indicator)) == 6


def test_imf_gaps_are_not_invented_nulls(populated, tmp_path):
    assert import_imf(populated, tmp_path, "missing_year").records_processed == 12


def test_imf_requires_registered_world_bank_countries(db, tmp_path):
    with pytest.raises(ValueError, match="World Bank first"):
        import_imf(db, tmp_path)
    assert db.scalar(select(IngestionRun)).status == "failed"


def test_new_sources_reject_current_year_before_http(populated, tmp_path):
    from datetime import date

    with pytest.raises(ValueError, match="completed calendar"):
        asyncio.run(
            ingest_source(populated, None, ["USA"], 2023, date.today().year, tmp_path)
        )


def test_source_http_retries_transient_errors_and_rejects_permanent_errors(monkeypatch):
    calls = []

    async def no_wait(_):
        pass

    monkeypatch.setattr("ingestion.connectors.http.asyncio.sleep", no_wait)

    def handler(request):
        calls.append(request)
        return httpx.Response(429 if len(calls) == 1 else 200, json={"ok": True})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            source = SourceHTTP(client, "https://example.test")
            assert (await source.get("data")).json() == {"ok": True}
            assert len(source.raw_pages) == 1
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(403))
        ) as client:
            with pytest.raises(SourceError, match="403"):
                await SourceHTTP(client, "https://example.test").get("data")

    asyncio.run(run())
    assert len(calls) == 2
