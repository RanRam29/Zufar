# Quick drop-in patch

This patch fixes:
- Alembic not found in `start.sh` (now uses `python -m alembic` and activates venv if present).
- Missing Alembic in requirements.
- Alembic env configured for **PostgreSQL only** via `DATABASE_URL` and imports your `backend` models.
- Modern Alembic revision template with type hints.

## Files

- `requirements.txt`  – adds `alembic` and `python-dotenv`.
- `alembic/script.py.mako` – fixed template.
- `alembic/env.py` – loads `DATABASE_URL` from env, imports models, uses `SQLModel.metadata`.
- `alembic.ini` – minimal config; URL comes from env.
- `scripts/start.sh` – Bash launcher (Linux/macOS/WSL).
- `scripts/start.ps1` – PowerShell launcher (Windows).
- `.env.example` – fill in and rename to `.env`.

## Usage

1. Copy these files into your repo, keeping same relative paths.
2. On **Windows (PowerShell)**:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   Copy-Item .env.example .env
   # edit .env with your real DATABASE_URL
   .\scripts\start.ps1
   ```
3. On **Linux/macOS/WSL**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   # edit .env with your real DATABASE_URL
   bash scripts/start.sh
   ```

If you still see `ModuleNotFoundError: backend`, ensure the repo root is on `PYTHONPATH` when running Alembic.
This `env.py` already appends the repo root to `sys.path`.
