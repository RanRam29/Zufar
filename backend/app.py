import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from .db import engine
from .routes.auth import router as auth_router

app = FastAPI(title="Zufar API")
app.router.redirect_slashes = False

ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://zufar-frontend-t13k.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=86400,
)

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.on_event("startup")
async def on_startup():
    if (os.getenv("AUTO_CREATE_TABLES", "1") == "1") and            (os.getenv("DATABASE_URL", "sqlite:///dev.db").startswith("sqlite")):
        SQLModel.metadata.create_all(engine)

app.include_router(auth_router)
