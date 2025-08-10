import os
from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Configure it in Render.")

# Use psycopg3 driver; pre-ping to avoid stale connections
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def init_db() -> None:
    SQLModel.metadata.create_all(engine)  # replace with Alembic later

def get_session() -> Session:
    return Session(engine)
