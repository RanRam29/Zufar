# Backend DB Write Fix – Drop-in Patch

## What you got
- Modular models under `backend/users/` with a shared `Base` in `backend/db/base.py`.
- Explicit `db.commit()` on user registration flow.
- Unified DB URL normalization (Render/Heroku) for app and Alembic.
- Startup DB health log banner.

## How to use
1. Drop the `backend/` and `alembic/` folders into your project (merge/replace files as needed).
2. Ensure each `__init__.py` exists (already included here).
3. Set `DATABASE_URL` in your environment. Postgres example: `postgresql+psycopg://user:pass@host:5432/db?sslmode=require`
4. Migrations:
   ```bash
   alembic upgrade head
   ```
5. Run app. On startup you should see:
   ```
   DB INIT | mode=EXTERNAL_POSTGRES | url=host:port/db?sslmode=require
   DB connectivity OK
   ```

## Endpoints
- `POST /auth/register` – body: `{ "email": "...", "password": "...", "full_name": "..." }`
- `GET /debug/users_count` – quick verification (remove in prod).

## Notes
- Requires: `sqlalchemy>=2.0`, `passlib[bcrypt]`, `fastapi`, `uvicorn`, `psycopg[binary]` (for Postgres).


---
## Multiple Alembic heads – quick fix & proper fix
**Quick fix (already applied in `scripts/start.sh`):**
- Run `alembic upgrade heads` so all branches apply and the app boots.

**Proper fix (once, locally):**
1. Inspect heads:
   ```bash
   alembic heads --verbose
   ```
2. Merge them into a single head (example with two heads `revA` and `revB`):
   ```bash
   alembic merge -m "merge heads" revA revB
   ```
   (If more than two, list them all).
3. Commit the generated merge revision under `alembic/versions/` and redeploy.
