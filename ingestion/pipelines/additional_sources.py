"""Add provider data to countries already registered by the World Bank import."""

from datetime import date

from backend.app.models import Country
from ingestion.pipelines.runs import finish_run, record_failure, start_run
from ingestion.validation.records import normalize_iso3


async def ingest_source(db, connector, countries, start_year, end_year, raw_dir):
    requested = sorted({normalize_iso3(code) for code in countries})
    if not 1 <= len(requested) <= 60:
        raise ValueError("Request between 1 and 60 countries per run")
    if not 1960 <= start_year <= end_year < date.today().year:
        raise ValueError("Use completed calendar years, starting from 1960")
    run = start_run(
        db, connector.provider_name, connector.base_url, connector.license_notes
    )
    run_id = run.id
    try:
        country_records = []
        for code in requested:
            country = db.get(Country, code)
            if country is None:
                raise ValueError(
                    f"Import {code} from World Bank first to register its country metadata"
                )
            country_records.append(
                {
                    "iso3": code,
                    "name": country.name,
                    "region": country.region,
                    "income_group": country.income_group,
                }
            )
        dataset = await connector.download(requested, start_year, end_year)
        dataset["countries"] = country_records
        for code in requested:
            if not any(
                row["country_iso3"] == code and row["value"] is not None
                for row in dataset["observations"]
            ):
                raise ValueError(
                    f"No numeric {connector.provider_name} data for {code} in this period"
                )
        return finish_run(db, run, dataset, connector.raw_pages, raw_dir)
    except Exception as error:
        record_failure(db, run_id, error)
        raise
