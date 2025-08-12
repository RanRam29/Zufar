#!/usr/bin/env bash
set -e
pip install --no-cache-dir -r backend/requirements.txt
echo "=== Boot ==="
echo "=== Running Alembic migrations ==="
alembic upgrade head
echo "=== Starting Uvicorn ==="
python -m uvicorn backend.app:app --host 0.0.0.0 --port $PORT
