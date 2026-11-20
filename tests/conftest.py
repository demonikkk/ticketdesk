import os

# Set BEFORE importing the app so tests never touch real Postgres/S3.
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["STORAGE_BACKEND"] = "s3"
os.environ["S3_BUCKET"] = "test-bucket"
os.environ.pop("S3_ENDPOINT_URL", None)

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import User
from app.security import hash_password


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_client(client):
    client.post("/register", data={"username": "alice", "password": "password123"})
    r = client.post("/login", data={"username": "alice", "password": "password123"})
    assert r.status_code == 200
    return client


@pytest.fixture
def admin_client():
    with SessionLocal() as db:
        db.add(User(username="admin", password_hash=hash_password("adminpass123"), role="admin"))
        db.commit()
    c = TestClient(app)
    r = c.post("/login", data={"username": "admin", "password": "adminpass123"})
    assert r.status_code == 200
    return c