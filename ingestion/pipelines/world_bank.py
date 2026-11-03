"""Run a World Bank import: validate, download, archive, save, and record the result."""

import logging
from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import DataSource, IngestionRun
from backend.app.models.entities import now
from ingestion.connectors.world_bank import WorldBankClient
from ingestion.pipelines.world_bank_data import download_dataset
from ingestion.pipelines.world_bank_storage import (
    archive_download,
    get_dataset_version,
    save_dataset,
)
from ingestion.validation.records import normalize_iso3

logger = logging.getLogger("sovereign.ingestion")


def start_run(db: Session, source_url: str) -> IngestionRun:
    source = db.scalar(
        select(DataSource).where(DataSource.provider_name == "World Bank WDI")
    )
    if source is None:
        source = DataSource(
            provider_name="World Bank WDI",
            source_url=source_url,
            license_notes="World Bank datasets generally use CC BY 4.0; verify dataset-specific terms and third-party restrictions before redistribution.",
        )
        db.add(source)
        db.flush()

    run = IngestionRun(source_id=source.id)
    db.add(run)
    db.commit()  # Keep this audit row even if a later download or write fails.
    return run


def record_failure(db: Session, run_id: str, error: Exception) -> None:
    db.rollback()
    run = db.get(IngestionRun, run_id)
    run.status = "failed"
    run.finished_at = now()
    # Database exception messages can contain credentials, so retain only the type.
    run.error_message = (
        f"{type(error).__name__}: ingestion did not complete; see local command output"
    )
    db.commit()
    logger.error(
        "ingestion_failed run_id=%s error_type=%s", run_id, type(error).__name__
    )


async def ingest_world_bank(
    db: Session,
    connector: WorldBankClient,
    countries: list[str],
    start_year: int,
    end_year: int,
    raw_dir: Path,
) -> IngestionRun:
    requested = sorted({normalize_iso3(code) for code in countries})
    if not 1 <= len(requested) <= 60:
        raise ValueError("Request between 1 and 60 countries per run")
    if not 1960 <= start_year <= end_year <= date.today().year:
        raise ValueError("Invalid observation year range")

    run = start_run(db, connector.base_url)
    run_id = run.id
    source_id = run.source_id

    try:
        dataset = await download_dataset(connector, requested, start_year, end_year)
        version = get_dataset_version(dataset)
        raw_path = archive_download(
            raw_dir, run_id, version, dataset, connector.raw_pages
        )
        save_dataset(db, dataset, version, source_id, raw_path)

        run.status = "succeeded"
        run.finished_at = now()
        run.records_processed = len(dataset["observations"])
        run.dataset_version = version
        source = db.get(DataSource, source_id)
        source.last_checked_at = run.finished_at
        db.commit()  # Save metadata, observations, and success status together.
    except Exception as error:
        record_failure(db, run_id, error)
        raise

    logger.info(
        "ingestion_succeeded run_id=%s records=%s dataset_version=%s",
        run_id,
        run.records_processed,
        run.dataset_version,
    )
    return run
