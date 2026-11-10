# Reuse this checkout's local verification database

Docker was unavailable during implementation. A temporary PostgreSQL 17.11 binary package was downloaded under ignored `data/local-postgres-runtime/`, and an isolated cluster was initialized at `data/postgres-local/` on loopback port 55432. This is an optional development verification runtime, not a replacement for the documented Compose setup or a production dependency. It uses local trust authentication; keep it bound to loopback.

From the repository root, after the verification services have stopped:

```sh
data/local-postgres-runtime/node_modules/@embedded-postgres/darwin-arm64/native/bin/pg_ctl -D data/postgres-local -l data/postgres-local.log -o '-h 127.0.0.1 -p 55432 -k /private/tmp' start
source .venv/bin/activate
# The existing ignored .env points to port 55432.
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

With `frontend/dist` built, the complete app is served at `http://127.0.0.1:8000`; a Vite server is not required. To check the production startup script instead, run `bash startup.sh` from the activated environment. The original official observations and archived responses remain under `data/`; no re-import is necessary. If PostgreSQL is already running, do not start a second instance. `pg_ctl -D data/postgres-local status` checks it.

To run the PostgreSQL suite with this runtime:

```sh
TEST_DATABASE_URL='postgresql+psycopg://sovereign@127.0.0.1:55432/sovereign_risk' .venv/bin/python -m pytest -q
```

Stop the frontend/API with Ctrl+C. Stop only this isolated cluster with:

```sh
data/local-postgres-runtime/node_modules/@embedded-postgres/darwin-arm64/native/bin/pg_ctl -D data/postgres-local stop
```

To switch to Docker, copy `.env.example` to `.env` and follow the main README. That creates a separate database, which needs migrations and ingestion. Neither runtime nor official downloaded data are committed to Git. The binary package can be removed separately once the cluster is stopped and no longer needed.
