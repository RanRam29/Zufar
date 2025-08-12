import os
import logging
from typing import Generator, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger("app.db")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

def _normalize_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://") and "+psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    if "sslmode=" not in url and url.startswith("postgresql+psycopg://"):
        url = f"{url}{'&' if '?' in url else '?'}sslmode=require"
    return url

RAW_URL: Optional[str] = os.getenv("DATABASE_URL")
if RAW_URL:
    DATABASE_URL = _normalize_url(RAW_URL)
    ACTIVE_DB = "EXTERNAL_POSTGRES"
else:
    DATABASE_URL = "sqlite:///./dev.db"
    ACTIVE_DB = "SQLITE_FALLBACK"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
    echo=os.getenv("SQL_ECHO", "0") == "1",
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)

def _redact(url: str) -> str:
    try:
        return url.split("@")[-1]
    except Exception:
        return "REDACTED"

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def on_startup_db_check() -> None:
    logger.warning("DB INIT | mode=%s | url=%s", ACTIVE_DB, _redact(DATABASE_URL))
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("DB connectivity OK")
    except Exception as e:
        logger.exception("DB connectivity FAILED: %s", e)
