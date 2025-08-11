import os
import tempfile
from fastapi.testclient import TestClient

tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{tmp_db.name}"

from backend.app import app
from backend.core.db import engine
from backend.models.base import Base

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
client = TestClient(app)

def test_signup_and_login_success():
    payload = {"username": "alice","email": "alice@example.com","password": "S3cret!!"}
    r = client.post("/auth/signup", json=payload)
    assert r.status_code == 200, r.text
    assert r.json()["access_token"]
    r2 = client.post("/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert r2.status_code == 200, r2.text
    assert r2.json()["access_token"]

def test_signup_duplicate_email():
    payload = {"username": "bob","email": "dup@example.com","password": "pass1234"}
    assert client.post("/auth/signup", json=payload).status_code == 200
    r = client.post("/auth/signup", json={"username": "bob2","email": "dup@example.com","password":"pass1234"})
    assert r.status_code == 400
    assert "Email already registered" in r.text
