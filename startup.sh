#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# A production deployment must include the React build.
if [ ! -f frontend/dist/index.html ]; then
  echo "Frontend build missing. Run npm ci and npm run build in frontend/ first." >&2
  exit 1
fi

# Run migrations separately, not on every restart.
exec python -m uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1
