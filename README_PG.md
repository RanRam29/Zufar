# Zufar Backend (Postgres only)

## Setup
1. Create `.env` from `.env.example` and set `SECRET_KEY` and `DATABASE_URL`.
2. Install requirements: `pip install -r requirements.txt`
3. Run Alembic:
   ```bash
   alembic upgrade head
   ```
4. Run the server:
   ```bash
   uvicorn backend.app:app --host 0.0.0.0 --port 8000
   ```

## Auth Endpoints
- `POST /auth/register` — `{ "email": "...", "full_name": "optional", "password": "******" }`
- `POST /auth/login` — `{ "identifier": "<email>", "password": "******" }` → returns `{ access_token, token_type }`
