# backend/database.py
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Render מספק בד"כ DATABASE_URL בסביבה (כמו postgresql://... או postgresql+psycopg://...)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # לגיבוי/לוקאל – עדכן לפי הצורך
    # לדוגמה: "sqlite:///./dev.db" או "postgresql+psycopg://user:pass@host/db?sslmode=require"
    DATABASE_URL = "sqlite:///./dev.db"

# חיבור
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
