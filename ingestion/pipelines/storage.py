"""Store an immutable dataset and its original source responses."""

import hashlib
import json
from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import Country, DataSnapshot, Indicator, Observation
from backend.app.models.entities import now


def get_dataset_version(dataset: dict) -> str:
    # Identical data receives the same ID, regardless of when it is downloaded.
    content = json.dumps(
        dataset, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    return hashlib.sha256(content.encode()).hexdigest()


def archive_download(
    directory: Path,
    run_id: str,
    version: str,
    dataset: dict,
    source_pages: list[dict],
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{run_id}.json"
    archive = {
        "dataset_version": version,
        "retrieved_at": now().isoformat(),
        "pages": source_pages,
        "manifest": dataset,
    }
    path.write_text(json.dumps(archive, allow_nan=False), encoding="utf-8")
    return path


def save_indicators(db: Session, records: list[dict], source_id: int) -> dict[str, int]:
    indicator_ids = {}
    for record in records:
        indicator = db.scalar(select(Indicator).where(Indicator.code == record["code"]))
        if indicator is None:
            indicator = Indicator(**record, source_id=source_id)
            db.add(indicator)
        else:
            if indicator.source_id != source_id:
                raise ValueError("Indicator code belongs to a different source")
            for field, value in record.items():
                setattr(indicator, field, value)

        db.flush()
        indicator_ids[record["code"]] = indicator.id
    return indicator_ids


def save_observations(
    db: Session, records: list[dict], indicator_ids: dict[str, int], version: str
) -> None:
    retrieved_at = now()
    for record in records:
        revision = record["source_revision_date"]
        revision_date = date.fromisoformat(revision) if revision else None
        observation = Observation(
            country_iso3=record["country_iso3"],
            indicator_id=indicator_ids[record["indicator_code"]],
            observation_date=date.fromisoformat(record["observation_date"]),
            value=record["value"],
            publication_date=None,
            source_revision_date=revision_date,
            retrieved_at=retrieved_at,
            dataset_version=version,
        )
        db.add(observation)


def save_dataset(
    db: Session, dataset: dict, version: str, source_id: int, raw_path: Path
) -> None:
    if db.get(DataSnapshot, version) is not None:
        return  # Keep the first retrieval unchanged when a refresh is identical.

    for record in dataset["countries"]:
        db.merge(Country(**record))
    db.flush()

    indicator_ids = save_indicators(db, dataset["indicators"], source_id)
    snapshot = DataSnapshot(
        id=version,
        source_id=source_id,
        raw_path=str(raw_path),
        manifest={
            "countries": sorted(country["iso3"] for country in dataset["countries"]),
            "start_year": dataset["start_year"],
            "end_year": dataset["end_year"],
            "records": len(dataset["observations"]),
            "indicators": dataset["indicators"],
            "provider_metadata": dataset.get("provider_metadata", {}),
        },
    )
    db.add(snapshot)
    db.flush()
    save_observations(db, dataset["observations"], indicator_ids, version)
