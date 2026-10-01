import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import User
from app.auth.dependencies import get_current_user


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSession()
    fake_user = User(email="test@example.com", hashed_password="unused")
    session.add(fake_user)
    session.commit()
    session.refresh(fake_user)

    def override_get_db():
        try:
            yield session
        finally:
            pass

    def override_get_current_user():
        return fake_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    session.close()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_and_list_applications(client):
    resp = client.post("/applications", json={"company": "Acme", "job_title": "Backend Engineer"})
    assert resp.status_code == 200
    app_id = resp.json()["id"]
    assert resp.json()["status"] == "saved"

    resp = client.get("/applications")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["id"] == app_id


def test_update_application_status(client):
    resp = client.post("/applications", json={"company": "Acme", "job_title": "Engineer"})
    app_id = resp.json()["id"]

    resp = client.patch(f"/applications/{app_id}", json={"status": "applied"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "applied"


def test_update_nonexistent_application_returns_404(client):
    resp = client.patch("/applications/9999", json={"status": "applied"})
    assert resp.status_code == 404


def test_delete_application(client):
    resp = client.post("/applications", json={"company": "Acme", "job_title": "Engineer"})
    app_id = resp.json()["id"]

    resp = client.delete(f"/applications/{app_id}")
    assert resp.status_code == 204

    resp = client.get("/applications")
    assert resp.json() == []


def test_register_and_login_flow(client):
    resp = client.post("/auth/register", json={"email": "new@example.com", "password": "s3cret123"})
    assert resp.status_code == 201
    assert resp.json()["email"] == "new@example.com"

    resp = client.post("/auth/register", json={"email": "new@example.com", "password": "s3cret123"})
    assert resp.status_code == 400  # duplicate email rejected
