from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)


def normalize_country_code(value: object) -> object:
    if isinstance(value, str):
        return value.strip().upper()
    return value


ISO3 = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Z]{3}$"),
    BeforeValidator(normalize_country_code),
]


class CountryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    iso3: str
    name: str
    region: str
    income_group: str


class CountryPage(BaseModel):
    items: list[CountryOut]
    total: int
    limit: int
    offset: int


class IndicatorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    code: str
    name: str
    category: str
    unit: str
    source_id: int
    definition: str


class ObservationOut(BaseModel):
    country_iso3: str
    indicator_code: str
    indicator_name: str
    unit: str
    observation_date: date
    value: float | None
    publication_date: date | None
    source_revision_date: date | None
    retrieved_at: datetime
    dataset_version: str
    source: str
    source_url: str


class ObservationPage(BaseModel):
    items: list[ObservationOut]
    total: int
    limit: int
    offset: int


class YearFilter(BaseModel):
    start_year: int = Field(default=1960, ge=1960, le=2100)
    end_year: int = Field(default=2100, ge=1960, le=2100)

    @model_validator(mode="after")
    def ordered(self):
        if self.start_year > self.end_year:
            raise ValueError("start_year must not exceed end_year")
        return self


class CompareRequest(YearFilter):
    countries: list[ISO3] = Field(min_length=2, max_length=6)
    indicators: list[str] = Field(default_factory=list, max_length=6)

    @field_validator("countries")
    @classmethod
    def unique_countries(cls, value):
        if len(set(value)) != len(value):
            raise ValueError("Choose distinct countries")
        return value


class CompareResponse(BaseModel):
    countries: list[CountryOut]
    items: list[ObservationOut]
    model_status: Literal["unavailable"] = "unavailable"


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    country_iso3: ISO3
    as_of_date: date
    # Feature-level inference requires a validated versioned schema, not arbitrary inputs.


class ModelStatus(BaseModel):
    status: Literal["unavailable"] = "unavailable"
    risk_model: str = "Model Not Trained"
    downgrade_model: str = "Model Not Trained"
    predictions_available: int = 0
    reason: str = "No validated supervised artifacts or licensed historical rating targets are configured."


class Freshness(BaseModel):
    latest_successful_refresh: datetime | None
    latest_observation_year: int | None
    countries_with_data: int
    observation_count: int
    failed_runs: int
    frequency: str = "Annual observations; refresh time is not the observation year or publication date."


class ReportOut(BaseModel):
    country: CountryOut
    generated_at: datetime
    executive_summary: str
    latest_indicators: list[ObservationOut]
    limitations: list[str]
    model_status: ModelStatus


class MapCountryOut(CountryOut):
    value: float | None
    observation_year: int | None
    retrieved_at: datetime | None
    dataset_version: str | None


class MapDataOut(BaseModel):
    indicator: IndicatorOut
    year: int
    available_years: list[int]
    countries: list[MapCountryOut]
    source_name: str
    source_url: str
