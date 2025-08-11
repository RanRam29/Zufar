# FastAPI Service — Fixed (ORM + Frontend + Render-ready)

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export PORT=8000
# Optional DB (SQLite default): export DATABASE_URL=sqlite:///./local.db
# For Postgres on Render or elsewhere, use standard URL; normalization handled in code.
python -m uvicorn backend.app:app --host 0.0.0.0 --port $PORT --reload
```

Open http://localhost:8000  (redirects to /static/index.html)

## Notes
- Supports **Postgres** (via `psycopg`) and **SQLite** out of the box.
- Normalizes `DATABASE_URL` (converts `postgres://` → `postgresql+psycopg://`).

## Endpoints
- `GET /healthz` — service health
- `GET /events` — list events (count of participants)
- `GET /events/geocode?address=...` — demo geocode
- Static UI under `/static` (Dashboard + API Explorer)
