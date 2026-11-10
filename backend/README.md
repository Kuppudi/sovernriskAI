# SovereignRisk AI backend

FastAPI, SQLAlchemy, Alembic, and PostgreSQL.

From the repository root, with Docker Compose installed:

```sh
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock -e '.[dev]'
docker compose up -d --wait db
python -m alembic upgrade head
python -m uvicorn backend.app.main:app --reload
```

API docs: `http://127.0.0.1:8000/docs`. For production-style local use, build React with `npm --prefix frontend ci` and `npm --prefix frontend run build`, then run `bash startup.sh` from the activated Python environment. The complete app uses `http://127.0.0.1:8000`. For frontend development only, Vite can still run separately.

The API supports an empty database. Data collection is a separate feature. Model status and prediction endpoints explicitly report unavailable models; no score or probability is invented.

```sh
python -m pytest -q
python -m alembic check
```

Set `TEST_DATABASE_URL` to run tests against PostgreSQL. Tests create and remove their own temporary schemas. Keep credentials out of Git; `.env` is ignored.
