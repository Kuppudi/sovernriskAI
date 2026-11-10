# World Bank data engineering notebook

Open `data_extract.ipynb` in VS Code, Jupyter, or an existing Azure Machine Learning notebook environment. Use Python 3.12+; Python 3.13 matches CI and App Service. Verify the selected kernel version because existing Azure ML kernels can be older. Keep the repository available to the kernel. From the repository root, install into your selected Python environment:

```sh
python -m pip install -r requirements.lock -r notebooks/requirements.txt
```

Select that environment as the notebook kernel, restart it, and run the cells in order. For a standalone Jupyter browser interface you can additionally install `jupyterlab`; VS Code and Azure ML already provide a notebook interface. No Docker or additional Azure service is required by the file pipeline.

The default scope is the existing six World Bank WDI indicators, BRA/DEU/IND/JPN/USA/ZAF, and 2015–2025. The notebook teaches API pagination/retries, country filtering, data contracts, null/zero handling, raw/cleaned/curated layers, coverage profiling, versioned exports, checkpoints, revision overlap, and idempotent storage. It does not add other providers or train a model.

Outputs are saved under ignored `data/notebooks/world_bank/`:

```text
bronze/<run_id>/responses.json
silver/<dataset_version>/dataset.json
silver/<dataset_version>/observations.csv
silver/<dataset_version>/countries.csv
silver/<dataset_version>/indicators.csv
gold/<dataset_version>/country_year.csv
gold/<dataset_version>/coverage.csv
runs/<run_id>.json
state/<scope_id>.json
```

Use `FULL_REFRESH=False` to refresh a recent overlap after a successful first run. Explicit null revisions replace earlier numbers; old snapshots remain available. Perform full refreshes periodically because older history can also be revised. A run advances its state only after all exports finish. Run one writer at a time. Download timestamps and provider revision dates do not prove historical publication dates.

## Optional database loading

The notebook works without any database setting. `PREVIEW_DATABASE_TARGET=False` and `LOAD_TO_DATABASE=False` are the saved defaults. With both off, it never reads `DATABASE_URL` or contacts PostgreSQL.

Loading means copying the already extracted data into the application's existing PostgreSQL tables; it does not fetch the API again or deploy code. Supply `DATABASE_URL` through the kernel environment, never a saved cell. Run the preview switch first, review host/port/database without credentials, then explicitly enable loading in the following cell. The database must already be migrated. Private Azure PostgreSQL requires appropriate VNet/DNS connectivity or a VPN from the notebook environment.

Existing snapshot storage and run auditing make database inserts atomic and repeated snapshots idempotent. Database load time is distinct from the API retrieval time retained in the notebook run archive. Raw archives stay on the notebook filesystem and must be backed up with database rows; this load does not upload them to App Service or Blob Storage.

## Verification

Install the notebook extras before running its isolated fixture tests:

```sh
python -m pytest -q backend/tests/test_world_bank_notebook.py
```

Tests run code cells with explicitly synthetic API responses, isolated files, and a disposable test database. Normal backend-only environments skip these tests if notebook extras are absent. Committed notebook execution counts and outputs must remain empty.
