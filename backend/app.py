from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import os
from pathlib import Path

from backend.database import on_startup_db_check
from backend.routes import auth as auth_routes

app = FastAPI()

# --- CORS ---
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
origins = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def _startup():
    on_startup_db_check()

# --- Static (SPA) ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = Path(os.getenv('STATIC_DIR', PROJECT_ROOT / 'static')).resolve()
assets_path = STATIC_DIR / 'assets'
os.makedirs(assets_path, exist_ok=True)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = Path(os.getenv("STATIC_DIR", PROJECT_ROOT / "static")).resolve()

if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")
    @app.get("/", include_in_schema=False)
    async def root():
        index_path = STATIC_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return JSONResponse({"status": "up"}, 200)
    @app.get("/favicon.svg", include_in_schema=False)
    async def favicon():
        fav = STATIC_DIR / "favicon.svg"
        if fav.exists():
            return FileResponse(fav)
        return JSONResponse({"ok": True}, 200)
    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        # Fallback all unknown routes to SPA index
        index_path = STATIC_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return JSONResponse({"status": "up"}, 200)
else:
    @app.get("/", include_in_schema=False)
    def root():
        return {"status": "up"}

# --- Health ---
@app.get("/healthz", include_in_schema=False)
def healthz():
    return {"status": "ok"}

# --- API routers ---
app.include_router(auth_routes.router)
