import datetime as dt
from urllib.parse import parse_qs, urlparse

import bcrypt
import pytest

from app.database import SessionLocal
from app.models import PasswordResetToken, User
from app.routers import auth_router
from tests.conftest import STRONG_PASSWORD, register_and_login


@pytest.fixture
def sent_emails(monkeypatch):
    sent = []
    monkeypatch.setattr(auth_router, "send_password_reset_email", lambda to, url: sent.append((to, url)))
    return sent


def _token_from(url: str) -> str:
    return parse_qs(urlparse(url).query)["token"][0]


# --- Registration & password rules ---

@pytest.mark.parametrize("password, reason", [
    ("Sh0rt!", "at least 8 characters"),
    ("alllower1!", "an uppercase letter"),
    ("ALLUPPER1!", "a lowercase letter"),
    ("NoNumbers!!", "a number"),
    ("NoSpecial123", "a special character"),
    ("P@ssw0rd1", "commonly used"),
])
def test_register_rejects_weak_passwords(api, password, reason):
    resp = api.post("/auth/register", json={"email": "a@example.com", "password": password})
    assert resp.status_code == 422
    assert reason in resp.json()["detail"]


def test_register_rejects_password_containing_email(api):
    resp = api.post("/auth/register", json={"email": "jordan.lee@example.com", "password": "Jordan.Lee#2026"})
    assert resp.status_code == 422
    assert "email" in resp.json()["detail"]


def test_register_rejects_mismatched_confirmation(api):
    resp = api.post("/auth/register", json={
        "email": "a@example.com", "password": STRONG_PASSWORD, "confirm_password": STRONG_PASSWORD + "x"})
    assert resp.status_code == 422
    assert "don't match" in resp.json()["detail"]


def test_register_rejects_invalid_email(api):
    resp = api.post("/auth/register", json={"email": "not-an-email", "password": STRONG_PASSWORD})
    assert resp.status_code == 422


def test_register_normalizes_email_and_blocks_duplicates(api):
    resp = api.post("/auth/register", json={"email": "  Jane@Example.COM ", "password": STRONG_PASSWORD})
    assert resp.status_code == 201
    assert resp.json()["email"] == "jane@example.com"
    assert "password" not in resp.text and "hashed" not in resp.text

    resp = api.post("/auth/register", json={"email": "jane@example.com", "password": STRONG_PASSWORD})
    assert resp.status_code == 409


def test_passwords_are_stored_as_argon2id(api):
    register_and_login(api)
    with SessionLocal() as db:
        user = db.query(User).one()
        assert user.hashed_password.startswith("$argon2id$")
        assert STRONG_PASSWORD not in user.hashed_password


# --- Login, session, logout ---

def test_login_me_and_case_insensitive_email(api):
    register_and_login(api)
    resp = api.post("/auth/login", data={"username": "JANE@example.com", "password": STRONG_PASSWORD})
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer" and body["expires_in"] > 0

    me = api.get("/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "jane@example.com"


def test_login_wrong_password_is_generic(api):
    register_and_login(api)
    wrong = api.post("/auth/login", data={"username": "jane@example.com", "password": "Wrong!Pass1"})
    missing = api.post("/auth/login", data={"username": "nobody@example.com", "password": "Wrong!Pass1"})
    assert wrong.status_code == missing.status_code == 401
    assert wrong.json()["detail"] == missing.json()["detail"]


def test_login_is_rate_limited_after_repeated_failures(api):
    register_and_login(api)
    for _ in range(5):
        assert api.post("/auth/login", data={"username": "jane@example.com", "password": "Wrong!Pass1"}).status_code == 401
    blocked = api.post("/auth/login", data={"username": "jane@example.com", "password": STRONG_PASSWORD})
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers


def test_requests_without_valid_token_are_rejected(api):
    assert api.get("/auth/me").status_code == 401
    assert api.get("/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_logout_all_revokes_existing_tokens(api):
    headers = register_and_login(api)
    assert api.post("/auth/logout-all", headers=headers).status_code == 200
    assert api.get("/auth/me", headers=headers).status_code == 401


def test_legacy_bcrypt_hash_still_works_and_is_upgraded(api):
    legacy = bcrypt.hashpw(b"OldPassword1!", bcrypt.gensalt()).decode()
    with SessionLocal() as db:
        db.add(User(email="old@example.com", hashed_password=legacy))
        db.commit()
    resp = api.post("/auth/login", data={"username": "old@example.com", "password": "OldPassword1!"})
    assert resp.status_code == 200
    with SessionLocal() as db:
        assert db.query(User).filter_by(email="old@example.com").one().hashed_password.startswith("$argon2id$")


# --- Change password ---

def test_change_password_revokes_old_sessions(api):
    headers = register_and_login(api)
    new = "N3w!Password99"
    resp = api.post("/auth/change-password", headers=headers, json={
        "current_password": STRONG_PASSWORD, "new_password": new, "confirm_password": new})
    assert resp.status_code == 200
    assert api.get("/auth/me", headers=headers).status_code == 401  # old token revoked
    fresh = {"Authorization": f"Bearer {resp.json()['access_token']}"}
    assert api.get("/auth/me", headers=fresh).status_code == 200
    assert api.post("/auth/login", data={"username": "jane@example.com", "password": new}).status_code == 200


def test_change_password_requires_current_password(api):
    headers = register_and_login(api)
    resp = api.post("/auth/change-password", headers=headers, json={
        "current_password": "Wrong!Pass1", "new_password": "N3w!Password99", "confirm_password": "N3w!Password99"})
    assert resp.status_code == 400


# --- Forgot / reset password ---

def test_forgot_password_response_is_identical_for_unknown_email(api, sent_emails):
    register_and_login(api)
    known = api.post("/auth/forgot-password", json={"email": "jane@example.com"})
    unknown = api.post("/auth/forgot-password", json={"email": "nobody@example.com"})
    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    assert "token" not in known.text
    assert [to for to, _ in sent_emails] == ["jane@example.com"]


def test_reset_token_is_stored_hashed(api, sent_emails):
    register_and_login(api)
    api.post("/auth/forgot-password", json={"email": "jane@example.com"})
    token = _token_from(sent_emails[0][1])
    with SessionLocal() as db:
        row = db.query(PasswordResetToken).one()
        assert row.token_hash != token and len(row.token_hash) == 64


def test_full_reset_flow_and_single_use(api, sent_emails):
    headers = register_and_login(api)
    api.post("/auth/forgot-password", json={"email": "jane@example.com"})
    to, url = sent_emails[0]
    assert url.startswith("http://localhost:5173/reset-password?token=")
    token = _token_from(url)

    assert api.post("/auth/reset-password/validate", json={"token": token}).status_code == 200

    new = "Res3t!Password"
    resp = api.post("/auth/reset-password", json={"token": token, "password": new, "confirm_password": new})
    assert resp.status_code == 200

    # Old session revoked, new password works, old one doesn't.
    assert api.get("/auth/me", headers=headers).status_code == 401
    assert api.post("/auth/login", data={"username": "jane@example.com", "password": new}).status_code == 200
    assert api.post("/auth/login", data={"username": "jane@example.com", "password": STRONG_PASSWORD}).status_code == 401

    # Token can't be reused.
    again = api.post("/auth/reset-password", json={"token": token, "password": "An0ther!Pass", "confirm_password": "An0ther!Pass"})
    assert again.status_code == 400


def test_reset_rejects_expired_token(api, sent_emails):
    register_and_login(api)
    api.post("/auth/forgot-password", json={"email": "jane@example.com"})
    token = _token_from(sent_emails[0][1])
    with SessionLocal() as db:
        row = db.query(PasswordResetToken).one()
        row.expires_at = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) - dt.timedelta(minutes=1)
        db.commit()
    resp = api.post("/auth/reset-password", json={"token": token, "password": "Res3t!Password", "confirm_password": "Res3t!Password"})
    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"]


def test_new_reset_request_invalidates_previous_link(api, sent_emails):
    register_and_login(api)
    api.post("/auth/forgot-password", json={"email": "jane@example.com"})
    api.post("/auth/forgot-password", json={"email": "jane@example.com"})
    first, second = (_token_from(url) for _, url in sent_emails)
    assert api.post("/auth/reset-password/validate", json={"token": first}).status_code == 400
    assert api.post("/auth/reset-password/validate", json={"token": second}).status_code == 200


def test_reset_rejects_weak_or_mismatched_password(api, sent_emails):
    register_and_login(api)
    api.post("/auth/forgot-password", json={"email": "jane@example.com"})
    token = _token_from(sent_emails[0][1])
    weak = api.post("/auth/reset-password", json={"token": token, "password": "weakpass", "confirm_password": "weakpass"})
    assert weak.status_code == 422
    mismatch = api.post("/auth/reset-password", json={"token": token, "password": "Res3t!Password", "confirm_password": "Res3t!Passwor"})
    assert mismatch.status_code == 422


def test_reset_rejects_garbage_token(api):
    resp = api.post("/auth/reset-password", json={"token": "x" * 43, "password": "Res3t!Password", "confirm_password": "Res3t!Password"})
    assert resp.status_code == 400


def test_forgot_password_email_rate_limit_keeps_generic_response(api, sent_emails):
    register_and_login(api)
    responses = [api.post("/auth/forgot-password", json={"email": "jane@example.com"}) for _ in range(5)]
    assert all(r.status_code == 202 for r in responses)
    assert len(sent_emails) == 3  # per-email cap, silently enforced


def test_client_ip_ignores_spoofable_headers_locally_and_uses_proxy_ip_on_render(monkeypatch):
    from starlette.requests import Request
    from app.utils.rate_limit import client_ip

    def make(headers):
        return Request({"type": "http", "client": ("10.0.0.1", 1234),
                        "headers": [(k.encode(), v.encode()) for k, v in headers.items()]})

    spoofed = {"x-forwarded-for": "1.2.3.4, 203.0.113.9"}
    assert client_ip(make(spoofed)) == "10.0.0.1"  # local: headers not trusted

    monkeypatch.setenv("RENDER", "true")
    assert client_ip(make(spoofed)) == "203.0.113.9"  # rightmost, not attacker-chosen leftmost
    assert client_ip(make({**spoofed, "cf-connecting-ip": "198.51.100.7"})) == "198.51.100.7"


def test_reset_token_cannot_be_claimed_twice_in_a_race(api, sent_emails, monkeypatch):
    """Simulates a second request using the link between our lookup and claim."""
    register_and_login(api)
    api.post("/auth/forgot-password", json={"email": "jane@example.com"})
    token = _token_from(sent_emails[0][1])
    real_lookup = auth_router._get_valid_reset_token

    def lookup_then_lose_race(db, tok):
        row = real_lookup(db, tok)
        with SessionLocal() as other:
            other.query(PasswordResetToken).filter_by(id=row.id).update(
                {PasswordResetToken.used_at: dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)})
            other.commit()
        return row

    monkeypatch.setattr(auth_router, "_get_valid_reset_token", lookup_then_lose_race)
    new = "Res3t!Password"
    resp = api.post("/auth/reset-password", json={"token": token, "password": new, "confirm_password": new})
    assert resp.status_code == 400
    # The original password still works: the losing request changed nothing.
    assert api.post("/auth/login", data={"username": "jane@example.com", "password": STRONG_PASSWORD}).status_code == 200


def test_rate_limiter_forgets_expired_keys(monkeypatch):
    from app.utils.rate_limit import RateLimiter

    limiter = RateLimiter(max_events=2, window_seconds=60)
    clock = [1000.0]
    monkeypatch.setattr("app.utils.rate_limit.time.monotonic", lambda: clock[0])
    limiter.hit("a")
    limiter.hit("a")
    assert limiter.retry_after("a") > 0
    assert limiter.retry_after("never-seen") == 0
    assert "never-seen" not in limiter._events  # lookups don't create entries
    clock[0] += 61
    assert limiter.retry_after("a") == 0
    assert "a" not in limiter._events

    limiter.SWEEP_THRESHOLD = 3
    for key in ("x", "y", "z"):
        limiter.hit(key)
    clock[0] += 61
    limiter.hit("fresh")  # triggers a sweep of the expired x/y/z
    assert set(limiter._events) == {"fresh"}
