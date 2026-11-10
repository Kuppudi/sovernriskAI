# One Azure App Service

React and FastAPI run together in one Linux Python App Service. PostgreSQL remains a separate database. This repository prepares a deployment package; it does not create or configure Azure resources automatically.

## 1. Build and check locally

From the repository root, with the Python environment active and PostgreSQL configured:

```sh
npm --prefix frontend ci
npm --prefix frontend run build
python -m pytest -q
python scripts/package_app_service.py
bash startup.sh
```

Open `http://127.0.0.1:8000`. Check `/`, `/countries/IND`, `/reports`, `/docs`, `/health`, and `/api/models/status`. The health endpoint requires a reachable, migrated PostgreSQL database. A new empty database shows no imported countries until ingestion runs.

`dist/app-service.zip` contains the built frontend and Python source at the correct ZIP root. Do not upload GitHub's Download ZIP or your local virtual environment. Node is needed to build React, not to run the deployed app.

## 2. Configure your existing Azure App Service

Use a Linux Python App Service (Python 3.13 matches CI). Start with B1 if its memory and cost suit the workload; confirm the available runtime and price in your region.

Set the startup command to:

```sh
bash startup.sh
```

Set these in **Settings → Environment variables**:

| Setting | Value |
|---|---|
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` — installs the Python requirements during ZIP deployment |
| `DATABASE_URL` | PostgreSQL connection URL, with psycopg, encoded credentials, and TLS; for example `postgresql+psycopg://USER:PASSWORD@HOST:5432/sovereign_risk?sslmode=require` |
| `CORS_ORIGINS` | `[]` for this same-origin app, or a JSON list of explicitly allowed separate development origins |
| `RAW_DATA_DIR` | `/home/sovereignrisk/raw` for persistent local archives in this initial version |

Keep `FRONTEND_DIR` unset so the app finds its packaged frontend automatically. No `VITE_API_BASE_URL` is used. Do not enable `WEBSITE_RUN_FROM_PACKAGE`; Python source ZIPs need build automation instead. Keep HTTPS enabled and configure database network access for the App Service. Restrict database permissions and use verified TLS certificates for production.

Store database credentials through Key Vault references where available. Managed-identity database authentication needs a token-aware connection implementation; this conversion does not add one. Blob-backed archives and production authentication remain later features.

## 3. Apply migrations and import data

From a configured release environment that can reach PostgreSQL:

```sh
python -m alembic upgrade head
python -m ingestion.cli --countries USA IND BRA DEU JPN ZAF --start-year 2015 --end-year 2025
```

The application must be deployed and its dependencies installed before running these commands from an App Service terminal. Use the deployed application's working directory and Python environment. Migrations are not run automatically on every restart. Raw data stays outside the deployment ZIP; back up archives and database rows together. Run one ingestion job at a time.

## 4. Deploy manually from GitHub

Pushes and pull requests run the **App Service** workflow to build, test, and upload an artifact named `app-service`. They do not deploy to Azure. You can download `app-service.zip` from the successful workflow run for your own ZIP deployment.

For the optional GitHub deployment job:

1. Create a GitHub environment named `azure-app-service`. Add a required reviewer if you want a manual approval gate.
2. Configure an Azure identity with permission to deploy to the existing web app. Add its GitHub OIDC federated credential with issuer `https://token.actions.githubusercontent.com`, audience `api://AzureADTokenExchange`, and subject `repo:Kuppudi/sovernriskAI:environment:azure-app-service`.
3. Add environment variables `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, and `AZURE_SUBSCRIPTION_ID` in that GitHub environment. These IDs are not passwords; no publish-profile secret is needed.
4. Open **GitHub → Actions → App Service → Run workflow**, choose `main`, and enter the existing App Service name. The workflow rebuilds the ZIP, signs in with OIDC, and deploys it. It creates no Azure resources.
5. Open the App Service HTTPS URL. Verify the home page, a refreshed country link, static files/map data, `/api/models/status`, and `/health`.

The previous Static Web Apps deployment workflow has been removed. Any already-created Static Web App remains in Azure until you choose to remove it; this change does not delete resources or repository secrets.

## Scope

This conversion changes hosting and packaging only. Models remain unavailable until validated artifacts exist. Future ML training can use `.ipynb` notebooks in Azure Machine Learning; App Service will load exported models. RAG follows afterward as a separate feature.

References: [Python App Service configuration](https://learn.microsoft.com/en-us/azure/app-service/configure-language-python), [Python ZIP deployment limitations](https://learn.microsoft.com/en-us/azure/app-service/deploy-run-package), [GitHub Actions deployment](https://learn.microsoft.com/en-us/azure/app-service/deploy-github-actions).
