# backend/db.py
import os
from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./casualties.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

def init_db() -> None:
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    return Session(engine)
