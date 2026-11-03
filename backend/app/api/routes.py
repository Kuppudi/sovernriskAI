from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import distinct, func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models import Country, IngestionRun, Indicator, Observation
from backend.app.schemas.api import (
    ISO3,
    CompareRequest,
    CompareResponse,
    CountryOut,
    CountryPage,
    Freshness,
    IndicatorOut,
    MapDataOut,
    ModelStatus,
    ObservationPage,
    PredictRequest,
    ReportOut,
    YearFilter,
)
from backend.app.services.map_data import get_map_data
from backend.app.services.exports import build_observation_csv
from backend.app.services.reports import build_country_report
from backend.app.services.observations import (
    observation_query,
    require_country,
    serialize_observation,
    validate_indicators,
)

router = APIRouter()
Db = Annotated[Session, Depends(get_db)]


@router.get("/api/data/map", response_model=MapDataOut, tags=["Indicators"])
def world_map(
    db: Db,
    indicator: str = Query(min_length=1, max_length=100),
    year: int = Query(ge=1960, le=2100),
):
    return get_map_data(db, indicator, year)


@router.get("/health", tags=["Operations"])
def health(db: Db):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(
            503,
            {
                "code": "DATABASE_UNAVAILABLE",
                "message": "Database is unavailable. Start PostgreSQL and run migrations.",
            },
        ) from None
    return {"status": "ok", "database": "connected", "version": "0.1.0"}


@router.get("/api/countries", response_model=CountryPage, tags=["Countries"])
def countries(
    db: Db,
    search: str = Query("", max_length=100),
    limit: int = Query(50, ge=1, le=250),
    offset: int = Query(0, ge=0),
):
    query = select(Country)
    if search:
        query = query.where(
            Country.name.icontains(search, autoescape=True)
            | Country.iso3.icontains(search, autoescape=True)
        )
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    return {
        "items": db.scalars(
            query.order_by(Country.name).offset(offset).limit(limit)
        ).all(),
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/api/countries/{iso3}", response_model=CountryOut, tags=["Countries"])
def country(iso3: ISO3, db: Db):
    return require_country(db, iso3)


@router.get("/api/indicators", response_model=list[IndicatorOut], tags=["Indicators"])
def indicators(db: Db):
    return db.scalars(select(Indicator).order_by(Indicator.code)).all()


@router.get(
    "/api/countries/{iso3}/indicators",
    response_model=ObservationPage,
    tags=["Indicators"],
)
def observations(
    iso3: ISO3,
    db: Db,
    years: Annotated[YearFilter, Query()],
    indicator: list[str] = Query(default=[], max_length=6),
    dataset_version: str | None = Query(None, pattern=r"^[a-f0-9]{64}$"),
    limit: int = Query(1000, ge=1, le=5000),
    offset: int = Query(0, ge=0),
):
    require_country(db, iso3)
    validate_indicators(db, indicator)
    query = observation_query(
        [iso3], indicator, years.start_year, years.end_year, dataset_version
    )
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    return {
        "items": [
            serialize_observation(row)
            for row in db.execute(query.offset(offset).limit(limit))
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/api/countries/{iso3}/indicators.csv", tags=["Indicators"])
def export_csv(
    iso3: ISO3,
    db: Db,
    years: Annotated[YearFilter, Query()],
    indicator: list[str] = Query(default=[], max_length=6),
):
    require_country(db, iso3)
    validate_indicators(db, indicator)
    rows = db.execute(
        observation_query([iso3], indicator, years.start_year, years.end_year)
    ).all()
    csv_content = build_observation_csv(rows)
    return Response(
        csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{iso3}-indicators.csv"'
        },
    )


@router.post("/api/compare", response_model=CompareResponse, tags=["Analysis"])
def compare(body: CompareRequest, db: Db):
    selected = [require_country(db, code) for code in body.countries]
    validate_indicators(db, body.indicators)
    rows = db.execute(
        observation_query(
            body.countries, body.indicators, body.start_year, body.end_year
        )
    ).all()
    return {
        "countries": selected,
        "items": [serialize_observation(row) for row in rows],
        "model_status": "unavailable",
    }


@router.get("/api/countries/{iso3}/report", response_model=ReportOut, tags=["Analysis"])
def report(iso3: ISO3, db: Db):
    return build_country_report(db, iso3)


@router.get("/api/models/status", response_model=ModelStatus, tags=["Models"])
def model_status():
    return ModelStatus()


def model_unavailable():
    raise HTTPException(
        503, {"code": "MODEL_NOT_TRAINED", "message": ModelStatus().reason}
    )


@router.get("/api/countries/{iso3}/prediction", tags=["Models"])
def prediction(iso3: ISO3, db: Db):
    require_country(db, iso3)
    model_unavailable()


@router.post("/api/predict", tags=["Models"])
def predict(body: PredictRequest, db: Db):
    require_country(db, body.country_iso3)
    model_unavailable()


@router.get("/api/data/freshness", response_model=Freshness, tags=["Operations"])
def freshness(db: Db):
    latest_observation = db.scalar(select(func.max(Observation.observation_date)))
    return {
        "latest_successful_refresh": db.scalar(
            select(func.max(IngestionRun.finished_at)).where(
                IngestionRun.status == "succeeded"
            )
        ),
        "latest_observation_year": latest_observation.year
        if latest_observation
        else None,
        "countries_with_data": db.scalar(
            select(func.count(distinct(Observation.country_iso3))).where(
                Observation.value.is_not(None)
            )
        ),
        "observation_count": db.scalar(select(func.count()).select_from(Observation)),
        "failed_runs": db.scalar(
            select(func.count())
            .select_from(IngestionRun)
            .where(IngestionRun.status == "failed")
        ),
    }
