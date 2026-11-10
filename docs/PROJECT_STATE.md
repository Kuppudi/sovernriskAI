# Project state · 2026-11-10

Delivery uses separate feature branches, each pushed and checked before merging to `main`. The user reports the existing app is running in Azure after manual Quick Deploy, private PostgreSQL configuration, and a 396-row World Bank import. The agent has not independently verified that Azure deployment or provisioned cloud resources.

## Latest feature · IMF ingestion

Branch `feature/imf-ingestion` adds four fiscal indicators from IMF DataMapper v2: WEO debt and overall balance, plus Fiscal Monitor primary balance and revenue. All use percent of GDP. IMF codes and original metadata remain separate from WDI. Unknown cutoffs, projection years, changed datasets/units, invalid values, and empty country scopes fail; earlier estimates and missing history remain explicitly disclosed. Country registration is reused from World Bank.

Shared `storage.py` and `runs.py` retain atomic writes, raw archives, immutable revisions, and import audits. The frontend uses actual provider attribution and units in the indicator map, country preview, comparison, and reports. Existing World Bank CLI commands remain compatible. No schema migration, new paid resource, training, or RAG is added.

Local evidence: 68 tests passed on PostgreSQL 17.11; frontend TypeScript/Vite production build passed. A live official IMF import added 264 observations for the existing six countries over 2015–2025, snapshot `b31850e3158a57314bb73478ccea6802920f481e2069ee8abe36cdf167a7da3e`. New data is local only; Azure still needs the new package and import command. See `DATA_IMPORTS.md`.

## Latest feature · single App Service

The conversion branch is `feature/single-app-service`, based on refreshed main `5d7f92c` (including the user's generated Static Web Apps workflow). React's compiled frontend and FastAPI now share one Python server and one URL. API requests and CSV exports are relative; no separate frontend/API origin is needed.

`backend/app/frontend.py` contains the small frontend-serving function. Known React URLs return index.html so direct links and refreshes work. `/api`, `/docs`, assets, and map files retain their own routes; missing API routes/assets stay 404s. Backend development still runs without a built frontend, while `startup.sh` refuses an incomplete production deployment.

`scripts/package_app_service.py` creates `dist/app-service.zip` with app code, migrations, requirements, the startup script, and built frontend. It excludes local data, credentials, node_modules, caches, and tests. The generated Static Web Apps workflow is removed; the new App Service workflow builds/packages on pushes and deploys only on an explicit manual run from main. No Azure resource, secret, or existing Static Web App is modified by this code change.

Local validation: 56 tests passed on SQLite and PostgreSQL 17.11, including shared hosting, direct links, missing assets/API routes, packaging exclusions, missing build rejection, and a fresh-process smoke test from an extracted real deployment ZIP. Production TypeScript/Vite build and shell syntax check passed; Alembic found no schema drift. The browser verified the whole app on Python port 8000, indicator history, country/report refreshes, and same-origin CSV links, with no console errors or warnings. No Vite server was running. Azure deployment remains unverified until the user configures an existing App Service and manually deploys. See `infrastructure/azure/README.md` for exact settings and steps.

The user requested ML training in `.ipynb` notebooks as the next separate feature, followed by RAG. No notebook or new ML training code is claimed by this hosting conversion; models remain explicitly unavailable.

## Current interface

App name: **SovereignRisk AI**. Main headline: **Sovereign Credit Risk**. The first page defaults to ML risk assessment, with a country selector, gray risk map, and a concise Not trained/Unavailable score panel. Promotional and instructional paragraphs have been removed. The Indicators view separately shows official economic values; these never populate risk scores. On phones, the ML panel appears before the map.

Intended use is sovereign lending/repayment-risk analysis for development-finance institutions, other lenders, and insurers. Repayment/default risk and rating-downgrade probability are separate targets. No trained model, repayment probability, credit score, or fabricated prediction is available.

## Feature delivery

1. `feature/ml-risk-homepage`: frontend, minimal ML homepage, indicator view, country selection, reports/data pages, frontend CI. Commit `dfc484a`; GitHub frontend build passed and the branch was merged/pushed to main first.
2. `feature/backend-api`: FastAPI, PostgreSQL schema/migrations, environment/Compose configuration, API services, backend CI. Commit `2bee0e7`; frontend/backend GitHub jobs and PostgreSQL migration cycle passed before main merge.
3. `feature/world-bank-ingestion`: official WDI connector, validation, source archives, snapshots, CLI, and data/API integration tests. Commit `878f415`; local full suite passed on SQLite/PostgreSQL. Both GitHub jobs also passed, including the PostgreSQL migration cycle, before main merge.
4. Project documentation, model limitations, and Azure planning notes are delivered separately after the functional features. These notes do not provision resources or implement model training.

## Code structure

`docs/CODE_GUIDE.md` explains the reading order. The ingestion command uses a short orchestrator, separate download/validation and storage modules, and explicit run auditing. Reports and CSV formatting are separate from HTTP handlers. The existing archived dataset identifier was verified unchanged by the readability refactor.

The world map bundles public-domain Natural Earth v5.1.2 outlines locally. Economic coverage remains six imported countries. `GET /api/data/map` returns latest-vintage observations for the exact selected year, with no older-value fallback.

Validation: 35 tests passed on SQLite and PostgreSQL 17.11; strict TypeScript/production build passed; schema check found no drift. Browser checks verified default unavailable risk state, country selection, indicator/risk separation, year changes, keyboard interaction, phone layout, and no page-level horizontal overflow. The compiled frontend had no browser warnings/errors. Current screenshot: ignored `data/ml-risk-homepage.jpg`. Verification services are stopped after checks; source and imported data remain available for restart.

## Milestone 1 · Implemented

React/TypeScript/Vite/Tailwind frontend; FastAPI/Pydantic API; SQLAlchemy models; Alembic migration; PostgreSQL Compose; environment examples; API connectivity and CORS; structured JSON request logs; consistent errors; persistent Copilot context. Actual PostgreSQL initialization, migration upgrade, and schema drift check passed using an isolated project-local PostgreSQL runtime because Docker was not installed. The Compose container itself has not been run.

## Milestone 2 · Implemented

World Bank WDI connector, six requested mappings, pagination and retry handling, finite numeric validation, explicit nulls, country/indicator metadata, atomic persistence, failed-run audits, raw JSON archives, content-addressed snapshots, incremental/overlapping refreshes, latest-vintage selection, country/indicator/year retrieval, freshness, and manual CLI. Publication dates stay unknown; provider response revision dates are preserved separately.

Live import succeeded for BRA, DEU, IND, JPN, USA, ZAF, 2015–2025: **396 observation records: 391 reported values and 5 explicit nulls**. Dataset snapshot: `af2ed7c32d049e5745d1e13a152b1cf30e6b38184245c7def8acf31bda67910f`. Original responses and database are ignored local artifacts. One temporary source failure was recovered through the connector retry path.

## Milestones 3–4 · Initial implementation, incomplete

The map home page, country selection, exact-year economic values, annual time-series charts, freshness, country analysis, comparison, explorer, CSV exports, and deterministic print-friendly country reports are implemented. Latest non-null report summaries disclose differing years and later gaps. Browser print/save-to-PDF is available; server-side PDF and report historical chart sections remain incomplete. Governance, debt, reserves, fiscal balance, and corruption datasets are explicitly absent. Broader coverage, automated UI regression/accessibility checks, and production UI refinements remain.

## Milestone 5 · Not started

Only reserved schema/directories and model card exist. No authorized ratings, target, training, calibration, backtesting, SHAP, or inference artifacts. Risk/downgrade API requests return explicit HTTP 503 `MODEL_NOT_TRAINED`; model status returns HTTP 200 unavailable. No arbitrary scores or synthetic production data.

## Milestone 6 · Single-service packaging implemented; Azure deployment pending

React/FastAPI shared hosting, startup script, a source ZIP packager, deployment documentation, and a manual OIDC deployment workflow now exist. Actual App Service provisioning/configuration, deployment, Blob storage integration, database managed-identity connection code, and Application Insights remain pending. No paid resources were created.

## Verification

- Foundation suite (Nov 3): **35 passed on SQLite and PostgreSQL 17.11**. The Nov 10 App Service suite expands this to **56 passing tests** on both databases, adding frontend routing and deployment-package verification.
- Strict TypeScript and final production frontend build: passed without bundle-size warnings after separating framework/chart chunks.
- PostgreSQL migration upgrade and final `alembic check`: passed; no drift. SQLite migration upgrade/downgrade/schema equivalence test passed. GitHub CI also passed a PostgreSQL downgrade/upgrade cycle on the backend feature branch.
- Python dependency consistency check: passed.
- Live frontend/proxy/API checks: HTTP 200 frontend/health/report; real-data freshness showed 6 countries and 396 records; prediction returned the expected HTTP 503.
- Browser checks passed for overview, country search, India analysis, India/USA comparison chart and tables, explorer country/year filters, CSV download, deterministic India report, print/save-PDF control, and explicit missing-data/model limitations. Print-to-PDF output itself was not generated or visually verified.
- Compiled production frontend preview: loaded and connected to the API with no browser console errors. Mobile/default and desktop layouts were inspected; checked viewport/content widths matched, with no page-level horizontal overflow. Comprehensive accessibility/device regression testing remains incomplete.
- A local preview screenshot is saved at ignored `data/dashboard-desktop.jpg`. Verification frontend/API/database services are stopped after checks; source, database, and raw downloads are retained for restart.
- Remote GitHub CI: frontend, backend, and ingestion feature checks verified passing before their main merges. Both workflows also run on main pushes.

## Known limitations and next steps

Complete milestone 3 QA/coverage first, then expand milestone 4 reports. Data availability and annual vintage limitations must remain visible. Ingestion supports a single writer; concurrent snapshot insert coordination and abandoned-run recovery are deferred. Current metadata can evolve; original metadata is recoverable in the raw manifest. Archive files must be backed up with database rows. No historical knowledge-at-time inference can be made from newly downloaded WDI history alone. Production authentication, rate limits, and deployment hardening are not yet implemented. Current test dependencies emit an upstream Starlette/httpx deprecation warning without test failures.

Use README for Docker setup or `docs/LOCAL_VERIFICATION.md` to reuse this session's downloaded PostgreSQL runtime. Do not confuse local build/runtime verification with Azure deployment.
