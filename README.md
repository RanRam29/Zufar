
# Casualty Management App – MVP

This is a full-stack minimal viable product you can run locally.

## Stack
- **Backend**: FastAPI + SQLModel (SQLite), Uvicorn, WebSocket broadcasts
- **Frontend**: Plain HTML + Fetch + WebSocket, Bootstrap 5
- **Auth**: Simple API key header (X-API-Key) for write actions (for demo)

## Quick Start (Windows)

1) Create a virtualenv (recommended) and install deps:
```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2) Run the backend:
```bat
uvicorn backend.app:app --reload
```

If `uvicorn` is not on PATH, use:
```bat
python -m uvicorn backend.app:app --reload
```

3) Open the UI:
- API docs (Swagger): http://127.0.0.1:8000/docs
- Web UI: http://127.0.0.1:8000/

## Demo API key
For any POST/PATCH endpoints, include header:
```
X-API-Key: devkey
```

## Project Structure
```
.
├─ backend/
│  ├─ app.py          # FastAPI app & routes
│  ├─ models.py       # SQLModel models
│  ├─ schemas.py      # Pydantic schemas
│  ├─ db.py           # DB init/session
│  └─ ws.py           # WebSocket manager
├─ frontend/
│  └─ index.html      # Minimal dashboard
└─ requirements.txt
```

## Notes
- This is an MVP. It’s production-aware but intentionally lean.
- Extend with auth (JWT), roles, and background jobs as needed.
=======
# Zufar
ZufaRav

