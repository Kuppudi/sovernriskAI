# Architecture decisions

## 2026-11-10 · Additional official data sources

Keep separate provider parsers and share only HTTP retries, storage, and run auditing. Register country metadata through the existing World Bank importer first. Namespace IMF codes by provider and dataset so different series cannot overwrite one another. No schema change is required. The UI reads source names and units from the API rather than assuming every value is World Bank data or a percentage.

IMF DataMapper v2 provides four initial fiscal series from WEO and Fiscal Monitor. Import only completed years before the provider's projection cutoff; fail if that cutoff is unknown. Earlier values can still be estimates. Preserve release metadata and unknown publication dates. Unlike WDI's rectangular response contract, IMF can omit unavailable years; keep those as gaps and require some numeric data for each requested country. The application remains a learning project with untrained models, not a point-in-time default model.

The user now manually deploys the built ZIP with Azure Quick Deploy. GitHub's deployment job can remain skipped; the artifact-build job is sufficient. New provider imports remain explicit commands, not web-startup tasks or scheduled Azure jobs.

## 2026-11-03 · Modular monorepo

Use the supplied repository root as the platform root. `backend/app` owns API/configuration/persistence; `ingestion` owns source connectors/validation/jobs; `frontend` owns the UI; `ml` is reserved for offline model work. No microservices or redundant wrapper directory. Synchronous SQLAlchemy sessions keep transactions straightforward; HTTPX handles asynchronous source I/O in the ingestion command. API queries run in FastAPI worker threads.

## 2026-11-03 · PostgreSQL persistence

Use PostgreSQL 17 through Compose, psycopg 3, SQLAlchemy 2, and explicit Alembic migrations. SQLite is the fast isolated test fallback. Startup never calls `create_all`. Database errors do not disclose URLs or credentials.

## 2026-11-03 · Snapshot and provenance design

Add `data_snapshots` to the requested schema with a SHA-256 content ID and raw-response path. Observation uniqueness includes this version to retain revisions. Each ingestion run has a durable independent audit record; country/indicator/snapshot/observation writes commit atomically. Identical snapshots reuse observations. Latest selection uses the last successful check time, so source reversions work without mutating retrieval timestamps. Original definitions and country metadata are recoverable from the archived normalized manifest. Backups must preserve archives and database rows together.

January 1 encodes an annual period, not an actual release date. WDI `lastupdated` is only a provider revision date; individual publication dates remain null. Retrieval vintages provide reproducibility, not proof of historical availability. Require an explicit value or null for each requested series/year; partial provider results fail the job. Only a single ingestion writer is supported; distributed locking and abandoned-run recovery are deferred.

## 2026-11-03 · Truthful modeling boundary

Both models are unavailable. No authorized ratings dataset, supervised target definition, historical-vintage evidence, calibrated model, or approved artifact is supplied. Reserved database rows alone cannot enable inference. Future serving must validate artifacts, feature schemas, metrics, calibration, target definition, and licensing. No arbitrary weighted score is exposed as a credit rating.

## 2026-11-03 · Frontend and reports

Vite proxies API calls locally; production uses an explicit API origin. TanStack Query owns server state; Recharts visualizes observations without connecting missing values. Deterministic Python reports disclose missing series and differing years. Browser print/save-to-PDF avoids a heavy PDF runtime in App Service B1. Full reporting and accessibility QA remain later milestones.

## 2026-11-03 · Deployment deferred

Prepare CI, environment examples, and Azure notes. Cloud resources and deployment remain deferred; source delivery follows the authorized feature-branch workflow below. Target Static Web Apps + Linux App Service B1 + PostgreSQL Flexible Server + Blob Storage. ML dependencies stay optional and outside the serving process until required.

## 2026-11-03 · Map first, with plain code and labels

The user's preferred entry point is an understandable world map, modeled on the World Bank data experience. Use a locally bundled Natural Earth SVG map with D3 geographic projection, rather than a paid map service or tile infrastructure. Keep indicator/year/country controls, exact-year values, a numeric color legend, and a short selected-country trend. The map palette describes indicator magnitude, never unvalidated sovereign risk. Other countries remain gray until real data is imported. Existing comparison, reports, and tables stay accessible from a simpler top navigation.

Add a single map-data API request instead of making a request for every country. The endpoint reuses latest-vintage selection and explicitly rejects unknown indicators/invalid years. Geography is independent of economic coverage and does not supply substitute data. Country selection includes imported countries even when they are absent from the coarse map outline.

Favor descriptive names, direct loops, and functions with one task. Split download/validation and snapshot storage from the ingestion orchestrator; move report and CSV formatting into their own service modules. Keep useful comments about atomicity, missing values, and dates. Provide a short code-reading guide instead of introducing new abstraction layers or frameworks.

## 2026-11-03 · Minimal ML-first homepage and sequential delivery

The user clarified that the main purpose is sovereign lending/repayment-risk analysis for development-finance institutions, other lenders, and insurers. Use the app name SovereignRisk AI and main headline Sovereign Credit Risk. Remove marketing copy and instructional paragraphs from the first page. Default to ML risk assessment, with a separate Indicators view. An economic growth or inflation value must never color a risk map or populate the risk score card. Until validated models exist, show a dash and a concise Not trained/Unavailable state. Keep detailed limitations in an expandable section; do not relabel downgrade probability as repayment probability.

The user authorized GitHub delivery feature by feature: frontend first, then backend foundation, then ingestion/integration. Each feature gets its own branch, local validation, push, CI verification, and main merge before the next starts. Do not publish all local work as one oversized change. Paid Azure provisioning remains unauthorized.

## 2026-11-10 · One App Service for React and FastAPI

The user authorized converting the code so the whole application runs in one Azure App Service. This supersedes the earlier Static Web Apps frontend architecture. PostgreSQL remains a separate database service; no paid resources are provisioned by the conversion.

Build React once with Vite, then serve its output from FastAPI. Register API routes first. Explicitly register the known React page URLs so saved links and browser refreshes return index.html, while unknown API paths, unknown pages, and missing assets retain real 404 responses. The frontend uses relative requests and CSV URLs; it needs no external API origin. Keep the optional Vite development server for local editing only.

Use a short startup script and an allowlisted ZIP packager. The ZIP includes source, migrations, requirements, and the compiled frontend, excluding credentials, local datasets, dependencies, and Git metadata. Fail packaging if the frontend is incomplete. CI also extracts a real package and verifies the HTML, assets, deep links, and API in a fresh Python process.

Replace the generated Static Web Apps workflow with an App Service build/package workflow. Pushes validate and upload an artifact only. An explicit manual run from main can deploy to an existing App Service using GitHub environment-scoped OIDC. The user controls resource setup, database configuration, and that deployment action. Migrations and ingestion stay separate from web-process startup.

The next ML feature should use `.ipynb` training notebooks for Azure Machine Learning. App Service will load exported validated model artifacts. RAG remains a later feature after model training and evaluation.
