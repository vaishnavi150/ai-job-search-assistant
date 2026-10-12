import os
import shutil
import sys
import tempfile

# Point the app at a throwaway database/index dir *before* app.config is
# imported, so tests never touch a developer's real data.
_tmp = tempfile.mkdtemp(prefix="ai-job-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_tmp, 'test.db')}"
os.environ["FAISS_INDEX_DIR"] = os.path.join(_tmp, "faiss")
os.environ["EMAIL_PROVIDER"] = ""
os.environ["LLM_PROVIDER"] = "groq"
os.environ["GROQ_API_KEY"] = "test-key"
os.environ.pop("RENDER", None)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app
from app.utils import rate_limit

STRONG_PASSWORD = "Str0ng!Passw0rd"


@pytest.fixture
def api():
    """A client against a fresh, empty database with real auth."""
    Base.metadata.drop_all(bind=engine)
    shutil.rmtree(os.environ["FAISS_INDEX_DIR"], ignore_errors=True)
    os.makedirs(os.environ["FAISS_INDEX_DIR"], exist_ok=True)
    for limiter in rate_limit.ALL_LIMITERS:
        limiter.clear()
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def register_and_login(client, email="jane@example.com", password=STRONG_PASSWORD) -> dict:
    resp = client.post("/auth/register", json={"email": email, "password": password, "confirm_password": password})
    assert resp.status_code == 201, resp.text
    resp = client.post("/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
