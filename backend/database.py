# backend/database.py
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


def _normalize_db_url(url: str | None) -> str:
    """
    Make sure the SQLAlchemy URL uses the psycopg (v3) driver.
    - Convert postgres:// -> postgresql://
    - Ensure driver is +psycopg (replace +psycopg2 if present)
    - Leave sqlite URLs as-is
    """
    if not url:
        return ""

    # Leave sqlite URLs untouched
    if url.startswith("sqlite:///") or url.startswith("sqlite://"):
        return url

    # Normalize old Heroku-style prefix
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]

    # If no explicit driver, add psycopg
    if url.startswith("postgresql://") and "+psycopg" not in url and "+psycopg2" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)

    # If psycopg2 was specified, switch to psycopg
    url = url.replace("postgresql+psycopg2://", "postgresql+psycopg://")

    return url


# Get DB URL from environment (Render usually sets DATABASE_URL)
_raw_url = os.getenv("DATABASE_URL", "")
DATABASE_URL = _normalize_db_url(_raw_url) or "sqlite:///./dev.db"

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)

# Dependency
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
