"""Validate SDMX CSV rows and normalize ADB's USD scales to millions."""

import csv
import io
import re
from datetime import date

from ingestion.connectors.http import SourceError
from ingestion.validation.records import ValidatedObservation


def parse_rows(csv_text, dataflow, selected_codes, country_codes, start_year, end_year):
    reader = csv.DictReader(io.StringIO(csv_text.lstrip("\ufeff")))
    required = {
        "DATAFLOW",
        "FREQ",
        "INDICATOR",
        "ECONOMY_CODE",
        "TIME_PERIOD",
        "OBS_VALUE",
        "UNIT",
        "UNIT_MULT",
        "OBS_STATUS",
    }
    if not required.issubset(reader.fieldnames or []):
        raise SourceError("ADB did not return the expected SDMX CSV columns")
    observations, metadata = {}, []
    for row in reader:
        code = row["INDICATOR"]
        country = country_codes.get(row["ECONOMY_CODE"])
        year = row["TIME_PERIOD"]
        if row["FREQ"] != "A" or code not in selected_codes or country is None:
            raise SourceError(
                "ADB returned an unexpected country, frequency, or indicator"
            )
        if not re.fullmatch(r"\d{4}", year) or not start_year <= int(year) <= end_year:
            raise SourceError("ADB returned a year outside the requested period")
        if not re.fullmatch(rf"ADB:{dataflow}\([\d.]+\)", row["DATAFLOW"]):
            raise SourceError("ADB returned an unexpected dataflow")
        if row["UNIT"] != "USD" or row["UNIT_MULT"] not in {"0", "3", "6", "9"}:
            raise SourceError("ADB changed its currency or unit multiplier")
        if row["OBS_STATUS"] not in {"", "A", "E", "P", "M"}:
            raise SourceError(
                "ADB observation status needs review; forecasts are not imported"
            )
        raw_value = row["OBS_VALUE"]
        # A missing value remains null; a reported zero remains zero.
        value = (
            None
            if raw_value in {"", ":"}
            else float(raw_value) * 10 ** (int(row["UNIT_MULT"]) - 6)
        )
        if row["OBS_STATUS"] == "M" and value is not None:
            raise SourceError("ADB marked a numeric observation as missing")
        observation = ValidatedObservation(
            country_iso3=country,
            indicator_code=f"ADB.{dataflow}.{code}",
            observation_date=date(int(year), 1, 1),
            value=value,
        ).model_dump(mode="json")
        key = (country, code, year)
        if key in observations:
            raise SourceError("ADB returned duplicate observations")
        observations[key] = observation
        metadata.append(
            {
                "country_iso3": country,
                "indicator_code": observation["indicator_code"],
                "year": year,
                **row,
            }
        )
    return list(observations.values()), metadata
