# backend/db.py
import os
from sqlmodel import SQLModel, create_engine, Session

# Expect: postgresql+psycopg://<user>:<pass>@<host>:5432/<db>
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Configure it in Render.")

# If you use an external (public) connection string on Render, force SSL:
connect_args = {}
if DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgresql+psycopg://"):
    # Optional: Render internal connection does not require sslmode, public does.
    if "sslmode=" not in DATABASE_URL:
        # You can append '?sslmode=require' if you use the public connection string.
        # DATABASE_URL += "?sslmode=require"
        pass

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def init_db() -> None:
    # For MVP: create tables at boot. For prod, switch to Alembic migrations.
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    return Session(engine)
