#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="${PYTHONPATH:-.}"
echo '=== Running Alembic migrations ==='
: "${ALEMBIC_UPGRADE_TARGET:=heads}"
AL_TGT="${ALEMBIC_UPGRADE_TARGET}"
echo "Using Alembic target: ${AL_TGT}"
alembic upgrade "${AL_TGT}"
echo '=== Starting Uvicorn ==='
python -m uvicorn backend.app:app --host 0.0.0.0 --port "${PORT:-8000}"
