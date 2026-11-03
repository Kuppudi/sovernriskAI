import math
import re
from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator


def normalize_iso3(value: str) -> str:
    normalized = value.strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", normalized):
        raise ValueError("Country code must contain three letters")
    return normalized


class ValidatedObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    country_iso3: str
    indicator_code: str
    observation_date: date
    value: float | None
    source_revision_date: date | None = None

    @field_validator("country_iso3")
    @classmethod
    def iso3(cls, value: str) -> str:
        return normalize_iso3(value)

    @field_validator("value", mode="before")
    @classmethod
    def numeric(cls, value):
        if value is None:
            return None
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ValueError("Observation must be a finite number or null")
        return value


def parse_observation(
    row: dict,
    indicator_code: str,
    revision: date | None,
    start_year: int,
    end_year: int,
) -> ValidatedObservation:
    if row.get("indicator", {}).get("id") != indicator_code:
        raise ValueError("Source returned an unexpected indicator")
    year = str(row.get("date", ""))
    if not re.fullmatch(r"\d{4}", year) or not start_year <= int(year) <= end_year:
        raise ValueError("Source observation year is outside the requested range")
    return ValidatedObservation(
        country_iso3=row.get("countryiso3code", ""),
        indicator_code=indicator_code,
        observation_date=date(int(year), 1, 1),
        value=row.get("value"),
        source_revision_date=revision,
    )
