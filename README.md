
# Zufar Portal (React + Vite + Tailwind) – Vercel Ready

## Quickstart (Local)
```bash
pnpm i   # or: npm i / yarn
pnpm dev # or: npm run dev
```
Environment:
```
VITE_API_BASE_URL=https://zufar.onrender.com
```
Visit http://localhost:5173

## Deploy to Vercel
- Import this repo in Vercel.
- Framework preset: **Vite**.
- Build Command: `npm run build`
- Output Dir: `dist`
- Environment Variable:
  - `VITE_API_BASE_URL=https://zufar.onrender.com` (or your backend URL)
- CORS: set `CORS_ORIGINS` in your backend to your Vercel domain.

## Notes
- Single-page app with static export.
- Registration form posts to `/auth/register` on your backend.
- Health badge calls `/healthz`.
