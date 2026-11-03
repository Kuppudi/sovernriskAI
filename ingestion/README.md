# World Bank data import

Run from the repository root after configuring PostgreSQL and applying migrations:

```sh
source .venv/bin/activate
python -m ingestion.cli --countries USA IND BRA DEU JPN ZAF --start-year 2015 --end-year 2025
```

The command downloads six official WDI indicators, stores observations in PostgreSQL, and archives original API responses under ignored `data/raw/`. Use 1–60 non-aggregate country codes per run. Refresh a smaller year range for incremental updates.

- `pipelines/world_bank.py` runs the steps and records the result.
- `pipelines/world_bank_data.py` downloads and validates records.
- `pipelines/world_bank_storage.py` archives responses and stores immutable dataset versions.
- `connectors/world_bank.py` handles HTTP retries and pagination.

Missing values remain null. Identical refreshes do not duplicate observations; changes preserve earlier versions. Observation years, retrieval times, and provider revision dates are separate fields. No supervised model targets or risk scores are manufactured from these economic values.

Run one import at a time. The local database and raw archives must be backed up together. Review World Bank dataset-specific licensing before redistribution.
