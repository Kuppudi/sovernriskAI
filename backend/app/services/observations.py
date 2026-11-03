from datetime import date

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models import Country, DataSource, Indicator, IngestionRun, Observation
from backend.app.schemas.api import ObservationOut


def require_country(db: Session, iso3: str) -> Country:
    country = db.get(Country, iso3)
    if country is None:
        raise HTTPException(
            404,
            {
                "code": "COUNTRY_NOT_FOUND",
                "message": "Country has not been ingested. Run the World Bank ingestion command.",
            },
        )
    return country


def validate_indicators(db: Session, codes: list[str]) -> None:
    if codes:
        known = set(db.scalars(select(Indicator.code).where(Indicator.code.in_(codes))))
        if set(codes) - known:
            raise HTTPException(
                422,
                {
                    "code": "UNKNOWN_INDICATOR",
                    "message": "One or more indicator codes have not been ingested.",
                },
            )


def observation_query(
    countries: list[str],
    codes: list[str],
    start_year: int,
    end_year: int,
    dataset_version: str | None = None,
):
    # A revision is selected per series/year. A latest null deliberately supersedes an old value.
    checks = (
        select(
            IngestionRun.dataset_version,
            func.max(IngestionRun.finished_at).label("last_seen"),
        )
        .where(IngestionRun.status == "succeeded")
        .group_by(IngestionRun.dataset_version)
        .subquery()
    )
    ranked = (
        select(
            Observation.id,
            func.row_number()
            .over(
                partition_by=(
                    Observation.country_iso3,
                    Observation.indicator_id,
                    Observation.observation_date,
                ),
                order_by=(
                    func.coalesce(checks.c.last_seen, Observation.retrieved_at).desc(),
                    Observation.id.desc(),
                ),
            )
            .label("rank"),
        )
        .outerjoin(checks, Observation.dataset_version == checks.c.dataset_version)
        .where(
            Observation.country_iso3.in_(countries),
            Observation.observation_date.between(
                date(start_year, 1, 1), date(end_year, 12, 31)
            ),
        )
    )
    if dataset_version:
        ranked = ranked.where(Observation.dataset_version == dataset_version)
    latest = ranked.subquery()
    query = (
        select(Observation, Indicator, DataSource)
        .join(latest, Observation.id == latest.c.id)
        .join(Indicator, Observation.indicator_id == Indicator.id)
        .join(DataSource, Indicator.source_id == DataSource.id)
        .where(latest.c.rank == 1)
    )
    if codes:
        query = query.where(Indicator.code.in_(codes))
    return query.order_by(
        Observation.country_iso3, Indicator.code, Observation.observation_date
    )


def serialize_observation(row) -> ObservationOut:
    observation, indicator, source = row
    return ObservationOut(
        country_iso3=observation.country_iso3,
        indicator_code=indicator.code,
        indicator_name=indicator.name,
        unit=indicator.unit,
        observation_date=observation.observation_date,
        value=observation.value,
        publication_date=observation.publication_date,
        source_revision_date=observation.source_revision_date,
        retrieved_at=observation.retrieved_at,
        dataset_version=observation.dataset_version,
        source=source.provider_name,
        source_url=source.source_url,
    )
