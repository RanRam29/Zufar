# Frontend enablement patch

## What you got
- `static/` folder with a minimal SPA (index.html + app.js + style.css).
- `backend/app.py` that:
  - Serves `/static` and returns `static/index.html` at `/`.
  - Exposes `/healthz`.
  - Enables CORS via `CORS_ORIGINS` env (defaults to `*`).
- Docker note to include `static/` in the image.

## How to use
1. Copy `static/` into your project root (same level as `backend/`).
2. Replace your `backend/app.py` with the provided one (or merge the changes).
3. If using Docker, ensure:
   ```dockerfile
   COPY static/ ./static/
   ```
4. Deploy. Visit `/` for UI, `/docs` for API.

## Separate Frontend (optional)
If you host a SPA elsewhere (Vercel/Netlify/Cloudflare Pages/GitHub Pages), set:
```
CORS_ORIGINS=https://your-frontend.example.com
```
in your backend environment.
