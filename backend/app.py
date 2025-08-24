import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.auth import router as auth_router

app = FastAPI(title="Zufar API", version="0.1.0")

default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://zufar-frontend-t13k.onrender.com",
]
env_origins = os.getenv("CORS_ORIGINS", "").strip()
origins = [o.strip() for o in env_origins.split(",") if o.strip()] or default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz")
def healthz():
    return {"ok": True}

app.include_router(auth_router, prefix="/auth", tags=["auth"])
