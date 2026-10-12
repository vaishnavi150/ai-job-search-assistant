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
    assert resp.json()["status"] == "ok"


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
    resp = client.post("/auth/register", json={"email": "new@example.com", "password": "S3cret!123"})
    assert resp.status_code == 201
    assert resp.json()["email"] == "new@example.com"

    resp = client.post("/auth/register", json={"email": "new@example.com", "password": "S3cret!123"})
    assert resp.status_code == 409  # duplicate email rejected


def test_invalid_status_is_rejected(client):
    resp = client.post("/applications", json={"company": "Acme", "job_title": "Engineer", "status": "hired"})
    assert resp.status_code == 422
    app_id = client.post("/applications", json={"company": "Acme", "job_title": "Engineer"}).json()["id"]
    assert client.patch(f"/applications/{app_id}", json={"status": "bogus"}).status_code == 422


def test_filter_by_status_and_job_url_validation(client):
    client.post("/applications", json={"company": "A", "job_title": "X", "status": "applied"})
    client.post("/applications", json={"company": "B", "job_title": "Y"})
    resp = client.get("/applications", params={"status": "applied"})
    assert [a["company"] for a in resp.json()] == ["A"]
    bad = client.post("/applications", json={"company": "C", "job_title": "Z", "job_url": "javascript:alert(1)"})
    assert bad.status_code == 422


def test_applications_are_scoped_to_owner(client):
    """A user can't read or change another user's rows."""
    from app.models import Application
    from app.database import get_db
    from app.main import app as fastapi_app
    db = next(fastapi_app.dependency_overrides[get_db]())
    other = User(email="other@example.com", hashed_password="unused")
    db.add(other)
    db.commit()
    row = Application(user_id=other.id, company="Secret", job_title="Hidden")
    db.add(row)
    db.commit()
    assert all(a["company"] != "Secret" for a in client.get("/applications").json())
    assert client.patch(f"/applications/{row.id}", json={"status": "offer"}).status_code == 404
    assert client.delete(f"/applications/{row.id}").status_code == 404
