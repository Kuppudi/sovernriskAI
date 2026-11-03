# Project state · 2026-11-03

Delivery uses separate feature branches, each pushed and checked before merging to `main`. No cloud deployment or paid Azure resources.

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

## Milestone 6 · Preparation only

Azure architecture/startup/configuration notes and validation CI exist. Resource definitions, deployment workflows, Blob storage integration, managed identity/Key Vault integration, Application Insights, and actual deployment remain unimplemented. No paid resources were created.

## Verification

- Final full suite: **35 passed on SQLite and 35 passed on PostgreSQL 17.11**, including map exact-year/missing/zero/revision behavior, idempotency, failure atomicity, null/zero validation, provider pagination/retries/errors, year/indicator filters, source revisions/reversions, snapshot queries, CSV, reports, comparison, CORS, and unavailable predictions.
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
