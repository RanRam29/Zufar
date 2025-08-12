# Zufar – Free-Tier Deploy Playbook

## Render (Free)
- **Backend** (Python Web Service):
  - Build: `pip install -r requirements.txt`
  - Start: `./scripts/start.sh`
  - Health: `/healthz`
  - Env:
    - `DATABASE_URL` (Render Postgres)
    - `ALEMBIC_UPGRADE_TARGET=head` (optional)
    - `LOG_LEVEL=INFO`

- **Frontend** (Static Site):
  - Build: `npm ci && npm run build`
  - Publish: `dist`
  - SPA routing: rewrite `/* -> /index.html`

## Vercel (Free)
- Framework: Vite
- Build: `npm ci && npm run build`
- Output: `dist`
- For API: set `VITE_API_BASE_URL=https://<render-backend-domain>` in Project → Settings → Environment Variables.

## Local
```bash
# backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=sqlite:///./dev.db
./scripts/start.sh

# frontend
npm ci
npm run dev
```
