#!/usr/bin/env bash
set -e
echo "=== Boot ==="
echo "=== Running Alembic migrations ==="
alembic upgrade head
echo "=== Starting Uvicorn ==="
python -m uvicorn backend.app:app --host 0.0.0.0 --port $PORT
