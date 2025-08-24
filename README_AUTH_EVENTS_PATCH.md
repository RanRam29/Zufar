Patch: Auth + Events stabilization (2025-08-24)

What this delivers
------------------
1. **Registration & Login** at `/auth/register` and `/auth/login` implemented with bcrypt (already in requirements) and a lightweight HMAC token.
2. **Events API** at `/events` with:
   - `POST /events` create (auth required)
   - `GET /events` list upcoming
   - `GET /events/historical` list archive
   - `POST /events/{id}/confirm` confirm attendance (auth required)
   - `PATCH /events/{id}` edit after enough confirmations (auth required)

Design principles
-----------------
- Zero removals of existing assets. Only three backend files were added/overwritten:
  - `backend/security_simple.py` (new)
  - `backend/routes/auth.py` (overwritten with a minimal, working version that uses `backend.users.models.User`'s `hashed_password` column)
  - `backend/routers/events.py` (overwritten with a fully working router based on `backend.models.event`)
  - `backend/app.py` modified to include the events router.
- No new external dependencies.

Environment
-----------
- Ensure `SECRET_KEY` is set in your environment. If missing, a dev default is used (not recommended for prod).
- Token expiry defaults to `ACCESS_TOKEN_EXPIRE_MINUTES=120` (can be overridden via env).

DB Notes
--------
- Users table expected: `backend.users.models.User` (table name: `user`, column: `hashed_password`).
- Events tables expected: `backend.models.event.Event` and `backend.models.event.Participant`.
- If your DB doesn’t have these tables yet, run your Alembic migrations accordingly.

How to test quickly
-------------------
1. **Register**: `POST /auth/register` body `{"full_name":"Test","email":"test@example.com","password":"secret123"}`
2. **Login**: `POST /auth/login` -> copy `access_token`
3. **Create event**: `POST /events` with `Authorization: Bearer <token>` and body including `title, description, address, start_time, end_time, lat, lng`.
4. **Confirm**: `POST /events/{id}/confirm` with `Authorization` header.
5. **Edit**: `PATCH /events/{id}` (allowed once confirmations >= `min_confirmations_for_edit`).

Rollback
--------
- To revert, restore your prior versions of the three touched files.
