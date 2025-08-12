from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from backend.database import on_startup_db_check
from backend.routes import auth as auth_routes
# debug route optional
# from backend.routes import debug as debug_routes

app = FastAPI()

# CORS (allow SPA from separate host if needed)
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
origins = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def _startup():
    on_startup_db_check()

# Static files & SPA index fallback
STATIC_DIR = os.getenv("STATIC_DIR", "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def root():
        index_path = os.path.join(STATIC_DIR, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
        return {"status": "up"}
else:
    @app.get("/", include_in_schema=False)
    def root():
        return {"status": "up"}

# health endpoint for Render
@app.get("/healthz", include_in_schema=False)
def healthz():
    return {"status": "ok"}

# API routers
app.include_router(auth_routes.router)
# app.include_router(debug_routes.router)
