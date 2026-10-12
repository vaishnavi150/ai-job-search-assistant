"""Email delivery (Brevo / not configured) and where reset links point.

requests.post is faked, so nothing is sent and no real key is needed.
"""
import logging

import pytest
import requests

from app.config import Settings, settings
from app.services import email as email_service
from tests.conftest import register_and_login

RESET_URL = "https://ai-job-assistant-web.onrender.com/reset-password?token=abc123"


class FakeResponse:
    def __init__(self, status_code, text=""):
        self.status_code = status_code
        self.text = text


@pytest.fixture
def brevo(monkeypatch):
    monkeypatch.setattr(settings, "email_provider", "brevo")
    monkeypatch.setattr(settings, "brevo_api_key", "xkeysib-test")
    monkeypatch.setattr(settings, "email_from", "noreply@example.com")
    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return fake_post.response

    fake_post.response = FakeResponse(201, '{"messageId":"<1@brevo>"}')
    monkeypatch.setattr(email_service.requests, "post", fake_post)
    return fake_post, calls


def test_brevo_request_shape(brevo, caplog):
    _, calls = brevo
    with caplog.at_level(logging.INFO):
        email_service.send_password_reset_email("jane@example.com", RESET_URL)

    assert len(calls) == 1
    url, kwargs = calls[0]
    assert url == "https://api.brevo.com/v3/smtp/email"
    assert kwargs["headers"]["api-key"] == "xkeysib-test"
    body = kwargs["json"]
    assert body["sender"] == {"email": "noreply@example.com", "name": "AI Job Search Assistant"}
    assert body["to"] == [{"email": "jane@example.com"}]
    assert RESET_URL in body["textContent"]
    assert 'href="https://ai-job-assistant-web.onrender.com/reset-password?token=abc123"' in body["htmlContent"]
    assert "30 minutes" in body["textContent"]
    assert "Password reset email sent" in caplog.text
    # Neither the link, the token nor the key may reach the logs.
    assert "abc123" not in caplog.text and "xkeysib" not in caplog.text


@pytest.mark.parametrize("status, text", [
    (401, '{"code":"unauthorized","message":"Key not found"}'),
    (400, '{"code":"invalid_parameter","message":"Sender is not valid"}'),
])
def test_brevo_rejection_is_logged_not_raised(brevo, caplog, status, text):
    fake_post, _ = brevo
    fake_post.response = FakeResponse(status, text)
    with caplog.at_level(logging.ERROR):
        email_service.send_password_reset_email("jane@example.com", RESET_URL)
    assert f"Brevo returned {status}" in caplog.text
    assert "abc123" not in caplog.text


def test_brevo_network_failure_is_logged_not_raised(brevo, monkeypatch, caplog):
    def boom(url, **kwargs):
        raise requests.ConnectionError("no route")
    monkeypatch.setattr(email_service.requests, "post", boom)
    with caplog.at_level(logging.ERROR):
        email_service.send_password_reset_email("jane@example.com", RESET_URL)
    assert "Couldn't reach Brevo" in caplog.text


def test_unconfigured_email_sends_nothing_and_warns(monkeypatch, caplog):
    monkeypatch.setattr(settings, "email_provider", "")
    monkeypatch.setattr(email_service.requests, "post", lambda *a, **k: pytest.fail("must not send"))
    with caplog.at_level(logging.WARNING):
        email_service.send_password_reset_email("jane@example.com", RESET_URL)
    assert "isn't configured" in caplog.text


def test_brevo_needs_both_key_and_sender():
    assert not Settings(email_provider="brevo", brevo_api_key="k", email_from="").email_enabled
    assert not Settings(email_provider="brevo", brevo_api_key="", email_from="a@b.co").email_enabled
    assert Settings(email_provider="brevo", brevo_api_key="k", email_from="a@b.co").email_enabled


def test_pasted_values_are_normalized(monkeypatch):
    monkeypatch.setenv("EMAIL_PROVIDER", " Brevo\n")
    monkeypatch.setenv("BREVO_API_KEY", "xkeysib-abc \n")
    monkeypatch.setenv("EMAIL_FROM", " noreply@example.com ")
    monkeypatch.setenv("FRONTEND_URL", " https://ai-job-assistant-web.onrender.com/ ")
    s = Settings()
    assert s.email_provider == "brevo"
    assert s.brevo_api_key == "xkeysib-abc"
    assert s.email_from == "noreply@example.com"
    assert s.email_enabled
    assert s.public_frontend_url == "https://ai-job-assistant-web.onrender.com"


def test_reset_link_base_url():
    web = "https://ai-job-assistant-web.onrender.com"
    # FRONTEND_URL wins; otherwise the first FRONTEND_ORIGIN, trailing slash dropped.
    assert Settings(frontend_origin=f"{web}/,http://localhost:5173").public_frontend_url == web
    assert Settings(frontend_origin="http://localhost:5173", frontend_url=f"{web}/").public_frontend_url == web


def test_forgot_password_emails_a_link_to_the_configured_frontend(api, brevo, monkeypatch):
    _, calls = brevo
    monkeypatch.setattr(settings, "frontend_url", "https://ai-job-assistant-web.onrender.com")
    register_and_login(api, "jane@example.com")

    resp = api.post("/auth/forgot-password", json={"email": "Jane@Example.com"})
    assert resp.status_code == 202

    assert len(calls) == 1
    body = calls[0][1]["json"]
    assert body["to"] == [{"email": "jane@example.com"}]
    assert "https://ai-job-assistant-web.onrender.com/reset-password?token=" in body["textContent"]
    # The token is only in the email, never in the API response.
    assert "token" not in resp.text


def test_forgot_password_for_unknown_email_sends_nothing(api, brevo):
    _, calls = brevo
    resp = api.post("/auth/forgot-password", json={"email": "nobody@example.com"})
    assert resp.status_code == 202
    assert calls == []
