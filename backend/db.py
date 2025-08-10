# backend/db.py
import os
from sqlmodel import SQLModel, create_engine, Session

# Require DATABASE_URL at runtime (Render env var)
# Expected form (Render internal connection):
#   postgresql+psycopg://<user>:<password>@<host>:5432/<db>
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Configure it in Render → Environment.")

# psycopg3 driver; pre-ping guards against stale connections
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def init_db() -> None:
    # MVP: auto-create tables. For production, replace with Alembic migrations.
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    return Session(engine)
