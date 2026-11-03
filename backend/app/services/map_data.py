"""One indicator, one year, and one value per country for the world map."""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import Country, DataSource, Indicator, Observation
from backend.app.schemas.api import IndicatorOut, MapCountryOut, MapDataOut
from backend.app.services.observations import observation_query


def get_map_data(db: Session, indicator_code: str, year: int) -> MapDataOut:
    indicator = db.scalar(select(Indicator).where(Indicator.code == indicator_code))
    if indicator is None:
        raise HTTPException(
            404,
            {
                "code": "INDICATOR_NOT_FOUND",
                "message": "This indicator has not been imported yet.",
            },
        )

    source = db.get(DataSource, indicator.source_id)
    countries = db.scalars(select(Country).order_by(Country.name)).all()
    country_codes = [country.iso3 for country in countries]

    # Exact-year values only. An older value must never silently fill a map gap.
    query = observation_query(country_codes, [indicator_code], year, year)
    observations = {
        observation.country_iso3: observation for observation, _, _ in db.execute(query)
    }

    available_dates = db.scalars(
        select(Observation.observation_date)
        .where(Observation.indicator_id == indicator.id)
        .distinct()
    ).all()
    available_years = sorted({day.year for day in available_dates}, reverse=True)

    map_countries = []
    for country in countries:
        observation = observations.get(country.iso3)
        map_countries.append(
            MapCountryOut(
                iso3=country.iso3,
                name=country.name,
                region=country.region,
                income_group=country.income_group,
                value=observation.value if observation else None,
                observation_year=year if observation else None,
                retrieved_at=observation.retrieved_at if observation else None,
                dataset_version=observation.dataset_version if observation else None,
            )
        )

    return MapDataOut(
        indicator=IndicatorOut.model_validate(indicator),
        year=year,
        available_years=available_years,
        countries=map_countries,
        source_name=source.provider_name,
        source_url=source.source_url,
    )
