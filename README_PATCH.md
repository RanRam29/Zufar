# Patch 2025-08-12
- Add `src/vite-env.d.ts` for Vite types so `import.meta.env` compiles.
- Move Python deps to `backend/requirements.txt` and include `email-validator` for Pydantic EmailStr.
- Render blueprint updated to point backend build to backend/requirements.txt and static FE service.
- Start script runs Alembic then Uvicorn.

**Important:** delete `/requirements.txt` from repo root if it exists.
