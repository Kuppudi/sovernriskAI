# Azure readiness · preparation only

No Azure resources, credentials, paid services, or deployment jobs are provisioned.

Target: React → Static Web Apps; API → Linux App Service B1; persistence → PostgreSQL Flexible Server; raw datasets/reports/model artifacts → Blob Storage. Application Insights is an optional budgeted addition.

Before deployment:

- Authorize and price the selected region, including PostgreSQL, backups, egress, storage, and logs. No current price assumptions are made.
- Build `frontend/` with `npm ci && npm run build` (output `frontend/dist/`). Set build-time `VITE_API_BASE_URL` to the API HTTPS origin. Configure SPA navigation fallback; the Vite proxy is local only.
- Deploy from the repository root with `requirements.txt`; start `python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 1`. Verify supported Azure Python versions before selection. Keep future models within B1 RAM.
- Set `DATABASE_URL` using psycopg and TLS (`sslmode=require` minimum; prefer verified CA/hostname), URL-encoded credentials, narrow database permissions, backups, and network controls. Run migrations as a controlled release step.
- Set `CORS_ORIGINS` as a JSON list of exact HTTPS frontend origins. Add production authentication/access policy, rate limiting, and operational controls.
- Replace local raw file paths with a Blob-backed adapter and durable object identifiers; align database and object backups.
- Prefer managed identities, Key Vault references, and GitHub OIDC. Add deployment workflows once concrete resources and environments are authorized. Existing CI performs checks only.
- Schedule ingestion separately (for example Azure Functions after runtime/time-budget validation). Keep a single writer until job coordination/recovery exists. Annual data does not require continuous polling.

No Container Apps, AKS, Redis, AI Search, Azure OpenAI, RAG, or chatbots. Milestone 6 remains incomplete; these notes do not constitute deployment.
