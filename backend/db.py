import os
from typing import Generator
from sqlmodel import SQLModel, create_engine, Session

def _normalize_pg_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = "postgresql+psycopg2://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url

def get_db_url() -> str:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is required (PostgreSQL only setup).")
    return _normalize_pg_url(db_url)

engine = create_engine(
    get_db_url(),
    pool_pre_ping=True,
    echo=False,
)

def create_all_if_enabled() -> None:
    if os.getenv("AUTO_CREATE_TABLES", "0") == "1":
        SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
