from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models.base import Base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
