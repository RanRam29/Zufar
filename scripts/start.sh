#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="${PYTHONPATH:-.}"
echo '=== Running Alembic migrations ==='
alembic upgrade head
echo '=== Starting Uvicorn ==='
python -m uvicorn backend.app:app --host 0.0.0.0 --port "${PORT:-8000}"
