#!/usr/bin/env bash
set -euo pipefail
echo "=== Boot ==="
# Move to repo root
cd "$(dirname "$0")/.."

# Activate venv if exists
if [ -f ".venv/bin/activate" ]; then
  . ".venv/bin/activate"
fi

# Load .env into env (DATABASE_URL, SECRET_KEY, etc.)
if [ -f ".env" ]; then
  set -a
  . ".env"
  set +a
fi

echo "=== Running Alembic migrations ==="
python -m alembic upgrade head

echo "=== Starting API ==="
exec uvicorn backend.app:app --host 0.0.0.0 --port "${PORT:-8000}"
