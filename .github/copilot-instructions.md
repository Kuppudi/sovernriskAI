# Sovereign Credit Risk Intelligence Platform

Read this file, `docs/PROJECT_STATE.md`, and `docs/DECISIONS.md` before changing the project.

- Mission: analyze documented sovereign economic and governance observations and, only when validated supervised models exist, sovereign risk and twelve-month downgrades.
- Stack: React, TypeScript, Vite, Tailwind, Recharts, TanStack Query; Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, HTTPX; PostgreSQL.
- Keep the modular monorepo layout. Execute Python modules from the repository root. Keep frontend contracts aligned with Pydantic response schemas.
- Write code that is easy for a person to read: descriptive names, direct control flow, small functions with one clear task, and comments explaining decisions. Avoid compressed one-liners, nested transformations, and unnecessary abstraction. Use `docs/CODE_GUIDE.md` as the reading path.
- Keep product copy minimal: app name and main headline, short functional labels, no promotional sentences. The first page highlights ML sovereign risk for lending/repayment analysis; economic indicators stay in a separate view. Downgrade probability is not repayment probability.
- Deliver one feature at a time: create a feature branch, verify locally, push it, check GitHub CI, then merge and push main before beginning the next feature. Never combine unrelated changes or commit credentials, downloaded data, or model artifacts.
- Use migrations, foreign keys, uniqueness constraints, parameterized SQLAlchemy queries, bounded pagination, explicit error responses, and environment-based CORS/configuration. Never expose credentials or accept arbitrary SQL.
- Preserve missing observations as null, not zero. Keep observation year, retrieval time, source metadata, source revision date when supplied, dataset versions, and original API responses. Never claim annual indicators are real-time.
- Never fabricate production data, model labels, ratings, probabilities, or feature explanations. Test fixtures must be isolated and explicitly synthetic. Models remain unavailable until trained, evaluated, calibrated as needed, and approved for inference.
- Training requires an explicit authorized target, agency/rating scope, chronological splits, knowledge-at-time features, baseline comparisons, calibration and discrimination evaluation, and artifact/schema metadata. Do not train inside API requests. Retrospectively downloaded observations are not historical information vintages.
- Prioritize local operation. Azure target: Static Web Apps, Linux App Service B1, PostgreSQL Flexible Server, Blob Storage, optional Application Insights. Never provision paid resources without explicit user authorization. Use managed identities/Key Vault where applicable. No AKS, Container Apps, Redis, RAG, chatbots, AI Search, or Azure OpenAI in the MVP.
- Run meaningful API, ingestion, validation, idempotency, and migration tests plus the frontend type check/build. Verify actual PostgreSQL when available; do not describe SQLite tests or offline SQL generation as PostgreSQL runtime verification.
- After each major milestone update PROJECT_STATE with completed/incomplete work, test evidence, bugs, and next steps. Record architectural decisions in DECISIONS.
