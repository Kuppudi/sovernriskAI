from datetime import UTC, date, datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.session import Base


def now() -> datetime:
    return datetime.now(UTC)


class Country(Base):
    __tablename__ = "countries"
    iso3: Mapped[str] = mapped_column(String(3), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    region: Mapped[str] = mapped_column(String(200))
    income_group: Mapped[str] = mapped_column(String(200))


class DataSource(Base):
    __tablename__ = "data_sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    provider_name: Mapped[str] = mapped_column(String(200), unique=True)
    source_url: Mapped[str] = mapped_column(Text)
    license_notes: Mapped[str] = mapped_column(Text)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Indicator(Base):
    __tablename__ = "indicators"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(300))
    category: Mapped[str] = mapped_column(String(100))
    unit: Mapped[str] = mapped_column(String(100))
    source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"))
    definition: Mapped[str] = mapped_column(Text)


class DataSnapshot(Base):
    __tablename__ = "data_snapshots"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"))
    raw_path: Mapped[str] = mapped_column(Text)
    manifest: Mapped[dict] = mapped_column(JSON)


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default="running", index=True)
    records_processed: Mapped[int] = mapped_column(default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    dataset_version: Mapped[str | None] = mapped_column(ForeignKey("data_snapshots.id"))


class Observation(Base):
    __tablename__ = "observations"
    __table_args__ = (
        UniqueConstraint(
            "country_iso3",
            "indicator_id",
            "observation_date",
            "dataset_version",
            name="uq_observation_vintage",
        ),
        Index(
            "ix_observation_series", "country_iso3", "indicator_id", "observation_date"
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    country_iso3: Mapped[str] = mapped_column(ForeignKey("countries.iso3"))
    indicator_id: Mapped[int] = mapped_column(ForeignKey("indicators.id"))
    observation_date: Mapped[date]
    value: Mapped[float | None]
    publication_date: Mapped[date | None]
    source_revision_date: Mapped[date | None]
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    dataset_version: Mapped[str] = mapped_column(ForeignKey("data_snapshots.id"))


class RatingEvent(Base):
    __tablename__ = "rating_events"
    __table_args__ = (
        UniqueConstraint(
            "country_iso3",
            "rating_agency",
            "instrument_or_issuer_type",
            "currency_basis",
            "effective_date",
            name="uq_rating_scope_date",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    country_iso3: Mapped[str] = mapped_column(ForeignKey("countries.iso3"), index=True)
    rating_agency: Mapped[str] = mapped_column(String(100))
    instrument_or_issuer_type: Mapped[str] = mapped_column(String(100))
    currency_basis: Mapped[str] = mapped_column(String(50))
    effective_date: Mapped[date]
    prior_rating: Mapped[str | None] = mapped_column(String(30))
    new_rating: Mapped[str] = mapped_column(String(30))
    event_type: Mapped[str] = mapped_column(String(30))


class ModelVersion(Base):
    __tablename__ = "model_versions"
    __table_args__ = (
        UniqueConstraint("model_name", "version", name="uq_model_version"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    model_name: Mapped[str] = mapped_column(String(100))
    version: Mapped[str] = mapped_column(String(100))
    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    artifact_location: Mapped[str] = mapped_column(Text)
    evaluation_metrics: Mapped[dict] = mapped_column(JSON)
    feature_schema: Mapped[dict] = mapped_column(JSON)


class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = (
        CheckConstraint(
            "downgrade_probability_12m IS NULL OR (downgrade_probability_12m >= 0 AND downgrade_probability_12m <= 1)",
            name="ck_prediction_probability",
        ),
        UniqueConstraint(
            "country_iso3",
            "as_of_date",
            "model_version_id",
            "data_snapshot_id",
            name="uq_prediction_snapshot",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    country_iso3: Mapped[str] = mapped_column(ForeignKey("countries.iso3"), index=True)
    as_of_date: Mapped[date]
    model_version_id: Mapped[int] = mapped_column(ForeignKey("model_versions.id"))
    risk_score: Mapped[float | None]
    downgrade_probability_12m: Mapped[float | None]
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    data_snapshot_id: Mapped[str] = mapped_column(ForeignKey("data_snapshots.id"))
