"""Build a country report from stored observations, using plain Python sentences."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from backend.app.models import Country
from backend.app.schemas.api import ModelStatus, ObservationOut, ReportOut
from backend.app.services.observations import (
    observation_query,
    require_country,
    serialize_observation,
)

REPORT_LIMITATIONS = [
    "Deterministic economic summary, not a credit rating or investment recommendation.",
    "Governance and default-outcome datasets are not implemented. IMF fiscal indicators appear only after their import runs.",
    "Indicators may have different latest years. Latest available non-null values are shown; later missing values are not estimates.",
    "First-publication dates are not supplied here. IMF historical values can include estimates. Retrieval vintages cannot establish historical availability.",
]


def get_latest_reported_values(db: Session, country_code: str) -> list[ObservationOut]:
    latest_values = {}
    query = observation_query([country_code], [], 1960, 2100)

    # The query orders each indicator by year. Keep its last non-missing value.
    for row in db.execute(query):
        observation = serialize_observation(row)
        if observation.value is not None:
            latest_values[observation.indicator_code] = observation

    return list(latest_values.values())


def write_summary(country: Country, observations: list[ObservationOut]) -> str:
    sentences = [
        f"{country.name} is classified by the World Bank in "
        f"{country.region}, {country.income_group}."
    ]
    if not observations:
        sentences.append("No non-missing economic observations are available.")

    for observation in observations:
        sentences.append(
            f"{observation.indicator_name}: {observation.value:,.2f} "
            f"{observation.unit} ({observation.observation_date.year})."
        )

    return " ".join(sentences)


def build_country_report(db: Session, country_code: str) -> ReportOut:
    country = require_country(db, country_code)
    observations = get_latest_reported_values(db, country_code)

    return ReportOut(
        country=country,
        generated_at=datetime.now(UTC),
        executive_summary=write_summary(country, observations),
        latest_indicators=observations,
        limitations=REPORT_LIMITATIONS,
        model_status=ModelStatus(),
    )
