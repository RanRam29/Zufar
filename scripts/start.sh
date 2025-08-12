#!/usr/bin/env bash
set -euo pipefail
echo "=== Boot ==="
if [[ -n "${ALEMBIC_UPGRADE_TARGET:-}" ]]; then
  echo "=== Running Alembic migrations ==="
  alembic upgrade "${ALEMBIC_UPGRADE_TARGET}"
fi
echo "=== Starting Uvicorn ==="
exec python -m uvicorn backend.app:app --host 0.0.0.0 --port "${PORT:-8000}"
