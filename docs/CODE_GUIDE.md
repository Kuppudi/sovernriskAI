# How to read the code

Start with one user action: **select a country and inspect its ML risk status**. Switch to Indicators to inspect economic observations separately. Follow the files below in order. Each file has one main responsibility.

## Frontend

1. `frontend/src/main.tsx` connects page URLs to their React components.
2. `frontend/src/components/Layout.tsx` draws the shared header, navigation, and footer.
3. `frontend/src/pages/MapExplorer.tsx` keeps the selected view, measure, year, and country. Risk and economic values are kept separate.
4. `frontend/src/components/RiskAssessment.tsx` loads model status and displays an unavailable score until a validated model is integrated.
5. `frontend/src/components/WorldMap.tsx` draws country outlines and handles clicks. It receives values as props; risk mode never uses economic values as scores.
6. `frontend/src/components/CountryPreview.tsx` shows economic values and history in the Indicators view.
7. `frontend/src/hooks/useData.ts` loads and caches API responses.
8. `frontend/src/services/mapData.ts` fetches map data and contains helpers for country choices, years, and colors.
9. `frontend/src/services/indicatorLabels.ts` holds measure names, units, and value formatting.

Country outlines are stored locally in `frontend/public/maps/world-countries.json`. This file contains geography only. It does not contain economic values.

## Backend

The frontend asks `GET /api/data/map?indicator=NY.GDP.MKTP.KD.ZG&year=2025` for values.

1. `backend/app/api/routes.py` reads the request and calls the appropriate service.
2. `backend/app/services/map_data.py` finds one value per country for that exact year.
3. `backend/app/services/observations.py` handles shared database queries and chooses the current source revision.
4. `backend/app/schemas/api.py` describes the response fields.
5. `backend/app/models/entities.py` describes the database tables.

Reports and CSV formatting have their own files: `services/reports.py` and `services/exports.py`. They are separate from HTTP routing so the report/export logic is easy to find and reuse.

## Importing official data

1. `ingestion/cli.py` reads the command-line options.
2. `ingestion/pipelines/world_bank.py` shows the import steps in order and records success or failure.
3. `ingestion/pipelines/world_bank_data.py` downloads and validates country, indicator, and observation records.
4. `ingestion/pipelines/world_bank_storage.py` creates the dataset version, archives original responses, and saves database rows.
5. `ingestion/connectors/world_bank.py` handles HTTP requests, retries, and pagination.

The import saves one audit record before doing the work. It commits the actual dataset only after validation and storage succeed. A failed import keeps its failure record but does not leave half a dataset in the database.

## Three rules that matter

- A missing value is `null`, never zero. Zero is a real value and appears on the map.
- A map for 2025 uses 2025 observations only. It cannot silently borrow a 2024 value.
- Color means a higher or lower number for the selected measure. It does not mean a validated credit-risk score, and it does not automatically mean good or bad.

The tests in `backend/tests/` cover those rules using isolated synthetic fixtures. Run them from the repository root with `.venv/bin/python -m pytest -q`.
