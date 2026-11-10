"""Record each import attempt and save a completed dataset in one transaction."""

import logging

from sqlalchemy import select

from backend.app.models import DataSource, IngestionRun
from backend.app.models.entities import now
from ingestion.pipelines.storage import (
    archive_download,
    get_dataset_version,
    save_dataset,
)


def start_run(db, provider, source_url, license_notes):
    source = db.scalar(select(DataSource).where(DataSource.provider_name == provider))
    if source is None:
        source = DataSource(
            provider_name=provider, source_url=source_url, license_notes=license_notes
        )
        db.add(source)
        db.flush()
    run = IngestionRun(source_id=source.id)
    db.add(run)
    db.commit()  # Keep an audit row even when a later download fails.
    return run


def finish_run(db, run, dataset, raw_pages, raw_dir):
    version = get_dataset_version(dataset)
    raw_path = archive_download(raw_dir, run.id, version, dataset, raw_pages)
    save_dataset(db, dataset, version, run.source_id, raw_path)
    run.status = "succeeded"
    run.finished_at = now()
    run.records_processed = len(dataset["observations"])
    run.dataset_version = version
    db.get(DataSource, run.source_id).last_checked_at = run.finished_at
    db.commit()
    return run


def record_failure(db, run_id, error):
    db.rollback()
    run = db.get(IngestionRun, run_id)
    run.status = "failed"
    run.finished_at = now()
    run.error_message = f"{type(error).__name__}: ingestion did not complete"
    db.commit()
    # Database error text can contain credentials; log only its type.
    logging.getLogger("sovereign.ingestion").error(
        "ingestion_failed run_id=%s error_type=%s", run_id, type(error).__name__
    )
