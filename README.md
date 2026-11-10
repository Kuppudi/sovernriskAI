# Sovereign Credit Risk Intelligence Platform

A local-first sovereign credit-risk application for lending and insurance analysis, built with React/TypeScript, FastAPI, and PostgreSQL. The first page highlights ML risk assessment; trained models remain unavailable. Official World Bank observations retain their provenance and revisions. **No credit ratings, model scores, repayment probabilities, or downgrade probabilities are fabricated.**

This repository root is the platform root, without a redundant wrapper directory. Read [project state](docs/PROJECT_STATE.md), [decisions](docs/DECISIONS.md), and [Copilot context](.github/copilot-instructions.md) before continuing.

For an easy reading path through the implementation, start with [how to read the code](docs/CODE_GUIDE.md).

## One App Service for the whole app

FastAPI now serves both the API and the built React frontend. Azure needs one Linux Python App Service, plus a separate PostgreSQL database. A Static Web App is not required.

After installing the Python dependencies and configuring the database below, run:

```sh
npm --prefix frontend ci
npm --prefix frontend run build
source .venv/bin/activate
bash startup.sh
```

Open [the complete app](http://127.0.0.1:8000). Pages, JavaScript, the map, API calls, and CSV downloads all use port 8000. Direct links such as `/countries/IND` also work after refreshing.

To create the deployment file:

```sh
python scripts/package_app_service.py
```

This writes `dist/app-service.zip`, containing the frontend build, backend, ingestion code, migrations, requirements, and startup script. Local credentials, raw data, tests, dependencies, and Git metadata are excluded. Follow the [App Service deployment steps](infrastructure/azure/README.md) for Azure settings and the optional manual GitHub deployment workflow. Creating the ZIP does not deploy anything.

## Local setup

Requires Python 3.12+ (3.13 recommended), Node 22.12+ or 24 LTS, and Docker with Compose. Execute from the repository root:

```sh
cp .env.example .env
# Keep DATABASE_URL consistent with POSTGRES_* if changing credentials.
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock -e '.[dev]'
docker compose up -d --wait db
python -m alembic upgrade head
python -m ingestion.cli --countries USA IND BRA DEU JPN ZAF --start-year 2015 --end-year 2025
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal:

```sh
cd frontend
npm ci
npm run dev
```

The commands above use Vite for development with automatic browser updates. Open [the development dashboard](http://127.0.0.1:5173), [API documentation](http://127.0.0.1:8000/docs), or [database health](http://127.0.0.1:8000/health). Production uses only the Python server, as described earlier. Schema changes use Alembic, never automatic table creation on startup. An empty migrated database is supported.

**This verification checkout:** Docker was absent, so an ignored project-local PostgreSQL runtime on port 55432 was used. The current ignored `.env` targets that runtime. For the Docker setup above, copy `.env.example` first. To reuse the downloaded runtime and existing official data, follow [local verification startup](docs/LOCAL_VERIFICATION.md).

## Working features

- Minimal ML-first landing page with a sovereign risk score panel and explicit not-trained/unavailable states. No slogan, promotional headline, or dummy score. Risk maps remain gray until model outputs exist.
- Separate indicator map with country/year controls, exact-year economic values, a numeric legend, and country history. Economic values are never treated as risk scores. Current economic coverage is six imported countries.
- Responsive navigation, optional source details, data tables, CSV downloads, country comparison, and initial deterministic print-friendly reports.
- Six WDI indicators: GDP growth, GDP per capita, inflation, exports/GDP, imports/GDP, and current account/GDP.
- Country/indicator metadata, pagination, retries for timeouts/429/5xx, finite numeric validation, atomic ingestion, durable run audits, raw response archives, and immutable snapshots.
- SQLAlchemy models and migrations for countries, indicators, observations, sources, ingestion runs, snapshots, rating events, model versions, and predictions.
- Explicit `MODEL_NOT_TRAINED` errors from prediction endpoints; no placeholder outputs.

## Refresh and reproducibility

```sh
python -m ingestion.cli --countries USA IND --start-year 2020 --end-year 2025
```

Request 1–60 recognized non-aggregate country codes. Refresh recent years incrementally or re-fetch a historical range; overlapping refreshes are supported. Schedule this same command later. Initially run only one ingestion process at a time.

Successful runs archive provider pages and normalized records in ignored `data/raw/`. SHA-256 snapshot IDs include normalized values, scope, provider revision dates, and definitions. Identical refreshes reuse observations; changed inputs create a new snapshot. Latest queries choose the last successfully checked vintage per series/year, including revised nulls and source reversions. First retrieval times stay immutable. Query `dataset_version` to recover a specific snapshot. Back up raw archives with the database.

Annual periods are stored as `YYYY-01-01`, not actual release dates. WDI `lastupdated` becomes `source_revision_date`, never first-publication date. Unknown publication dates remain null. Current downloads cannot establish historical knowledge-at-time; additional vintage evidence is required before backtesting.

## API

| Method | Route | Behavior |
|---|---|---|
| GET | `/health` | Database connectivity; HTTP 503 on failure |
| GET | `/api/countries` | `search`, `limit` (1–250), `offset` |
| GET | `/api/countries/{iso3}` | Normalized country code; 404 if not ingested |
| GET | `/api/countries/{iso3}/indicators` | Year range, repeated `indicator`, `dataset_version`, pagination |
| GET | `/api/countries/{iso3}/indicators.csv` | Filtered CSV; null values export as blank cells |
| GET | `/api/countries/{iso3}/report` | Deterministic report JSON |
| GET | `/api/countries/{iso3}/prediction` | HTTP 503 until validated models exist |
| GET | `/api/indicators` | Definitions and units |
| POST | `/api/compare` | 2–6 countries; year/indicator filters |
| POST | `/api/predict` | Validates country/as-of date; HTTP 503 |
| GET | `/api/models/status` | Unavailable status and explanation |
| GET | `/api/data/freshness` | Refresh date, latest year, stored-vintage count |
| GET | `/api/data/map` | One indicator and exact year across imported countries; `indicator` and `year` required |

Example comparison body: `{"countries":["USA","IND"],"indicators":["NY.GDP.MKTP.KD.ZG"],"start_year":2020,"end_year":2025}`. Observation pagination defaults to 1,000, maximum 5,000. Errors use `{"error":{"code":"...","message":"..."}}`; validation errors include field details. `/api` is the initial v1 contract; incompatible future versions use `/api/v2`.

## Checks

```sh
python -m pytest -q
python -m alembic check
cd frontend
npm run build
```

Tests use isolated, explicitly synthetic SQLite fixtures by default. To test PostgreSQL, use a database identity permitted to create temporary schemas:

```sh
TEST_DATABASE_URL='postgresql+psycopg://sovereign:local_dev_only@localhost:5432/sovereign_risk' python -m pytest -q
```

Each PostgreSQL test creates and removes its own schema. Frontend/backend CI exercise builds, tests, and migrations. App Service CI also checks shared hosting, builds the deployment ZIP, and verifies the real app from an extracted copy. Its deployment job runs only when manually requested from main. Features are pushed, checked, and merged into main one at a time. Python versions are locked in `requirements.lock`; frontend versions in `frontend/package-lock.json`. Future ML dependencies are optional (`.[ml]`) and excluded from API startup.

## Remaining work

Milestones 1–2 are implemented. Initial country dashboard, reporting, comparison, and export flows are usable; broader coverage and full dashboard/reporting QA remain. Governance, debt, fiscal balance, reserves, corruption, authorized ratings, ML training/evaluation/calibration/SHAP/inference, direct server-side PDF rendering, and Azure deployment are incomplete. PDF export currently uses browser print/save-to-PDF.

The local MVP has no authentication; development services bind to loopback. Production access control, hardening, Blob storage, monitoring, and deployment are later work. No paid resources, RAG, chatbots, AI Search, or Azure OpenAI are included. See [Azure notes](infrastructure/azure/README.md), [data dictionary](docs/DATA_DICTIONARY.md), and [model card](docs/MODEL_CARD.md).
