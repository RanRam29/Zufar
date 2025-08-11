# Event Console (IL) — FastAPI + Static SPA

Features:
- Map with current events (Leaflet + OSM)
- Sign-up / Login (JWT)
- Historical events page
- WebSocket notifications ("push-like") for new confirmations
- Israeli address geocoding via Nominatim
- Edit events gated by required attendee threshold
- Structured logging

## Run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PORT=8000
python -m uvicorn backend.app:app --host 0.0.0.0 --port $PORT --reload
```

## Env
- DATABASE_URL (sqlite default: sqlite:///./app.db)
- SECRET_KEY (change in production)

## Notes
- For real Web Push (VAPID), add a push service later; current impl uses WebSocket + Notification API.
- For participants listing, add /events/{id}/participants endpoint as needed.

---
## Alembic (DB migrations)
Initialize & upgrade:
```bash
alembic upgrade head
# Make changes to models, then:
alembic revision --autogenerate -m "change"
alembic upgrade head
```

## Security
- Protected routes: `POST /events`, `PATCH /events/{id}` require Bearer JWT.
- Public routes: signup/login, list/historical, confirm, participants.
