import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.app import app
from backend.models.base import Base
import backend.models.user  # noqa: F401 ensure model registration

# Configure a test database (SQLite in-memory)
SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
Base.metadata.create_all(bind=engine)

# Dependency override
from backend.database import get_db  # type: ignore

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_signup_and_login_flow():
    # Sign up
    resp = client.post("/auth/signup", json={
        "full_name": "Ran Ram",
        "email": "ran@example.com",
        "password": "secret123"
    })
    assert resp.status_code == 200, resp.text
    token = resp.json().get("access_token")
    assert token

    # Duplicate should fail
    resp2 = client.post("/auth/signup", json={
        "full_name": "Ran Again",
        "email": "ran@example.com",
        "password": "secret123"
    })
    assert resp2.status_code == 400

    # Login ok
    resp3 = client.post("/auth/login", json={
        "email": "ran@example.com",
        "password": "secret123"
    })
    assert resp3.status_code == 200
    assert resp3.json().get("access_token")
