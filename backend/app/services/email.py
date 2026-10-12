"""Outbound email for password resets.

Two providers, picked by EMAIL_PROVIDER:
- "brevo": Brevo's HTTP API (free tier: 300 emails/day). Use this on Render's
  free tier, which blocks outbound SMTP ports 25/465/587.
- "smtp": any SMTP server (Gmail app password, Mailtrap, etc.) - for local
  development or paid hosts.

Never logs message bodies: they contain single-use reset links.
"""
import html
import logging
import smtplib
import ssl
from email.message import EmailMessage

import requests

from app.config import settings

logger = logging.getLogger(__name__)


class EmailNotConfiguredError(RuntimeError):
    pass


class EmailSendError(RuntimeError):
    pass


def send_email(to: str, subject: str, text_body: str, html_body: str) -> None:
    if not settings.email_enabled:
        raise EmailNotConfiguredError("Email delivery isn't configured.")
    if settings.email_provider == "brevo":
        _send_brevo(to, subject, text_body, html_body)
    else:
        _send_smtp(to, subject, text_body, html_body)


def _send_brevo(to: str, subject: str, text_body: str, html_body: str) -> None:
    try:
        resp = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={"api-key": settings.brevo_api_key, "accept": "application/json"},
            json={
                "sender": {"email": settings.email_from, "name": settings.email_from_name},
                "to": [{"email": to}],
                "subject": subject,
                "textContent": text_body,
                "htmlContent": html_body,
            },
            timeout=20,
        )
    except requests.RequestException as exc:
        raise EmailSendError(f"Couldn't reach Brevo: {type(exc).__name__}") from exc
    if resp.status_code >= 300:
        # Brevo's error body describes config problems (unverified sender,
        # bad key); it never echoes our message content.
        raise EmailSendError(f"Brevo returned {resp.status_code}: {resp.text[:200]}")


def _send_smtp(to: str, subject: str, text_body: str, html_body: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{settings.email_from_name} <{settings.email_from}>"
    msg["To"] = to
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    context = ssl.create_default_context()
    try:
        if settings.smtp_port == 465:
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=20, context=context)
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20)
        with server:
            if settings.smtp_port != 465 and settings.smtp_use_tls:
                server.starttls(context=context)
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
    except (smtplib.SMTPException, OSError) as exc:
        raise EmailSendError(f"SMTP send failed: {type(exc).__name__}: {exc}") from exc


def send_password_reset_email(to: str, reset_url: str) -> None:
    """Meant to run as a background task, so failures are logged, not raised -
    the API response is identical whether or not the email went out."""
    minutes = settings.password_reset_token_minutes
    subject = "Reset your Nextrung password"
    text_body = (
        "We received a request to reset the password for your account.\n\n"
        f"Reset it here (the link expires in {minutes} minutes and works once):\n{reset_url}\n\n"
        "If you didn't ask for this, you can ignore this email - your password won't change."
    )
    safe_url = html.escape(reset_url, quote=True)
    html_body = f"""<!doctype html>
<html><body style="margin:0;background:#f2f6f6;font-family:-apple-system,Segoe UI,Roboto,sans-serif;color:#111c2b">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:32px 16px">
    <table role="presentation" width="100%" style="max-width:480px;background:#fff;border-radius:12px;padding:32px">
      <tr><td>
        <p style="margin:0 0 24px;font-size:20px;font-weight:800;letter-spacing:-0.5px">Next<span style="color:#0f766e">rung</span></p>
        <h1 style="font-size:20px;margin:0 0 16px">Reset your password</h1>
        <p style="font-size:15px;line-height:1.5;margin:0 0 24px">We received a request to reset the password for your Nextrung account.</p>
        <p style="margin:0 0 24px"><a href="{safe_url}" style="display:inline-block;background:#0f766e;color:#fff;text-decoration:none;padding:12px 20px;border-radius:8px;font-weight:600">Choose a new password</a></p>
        <p style="font-size:13px;line-height:1.5;color:#5b6577;margin:0 0 8px">This link expires in {minutes} minutes and can only be used once.</p>
        <p style="font-size:13px;line-height:1.5;color:#5b6577;margin:0">If you didn't request this, ignore this email - your password won't change.</p>
      </td></tr>
    </table>
  </td></tr></table>
</body></html>"""
    try:
        send_email(to, subject, text_body, html_body)
        logger.info("Password reset email sent")
    except EmailNotConfiguredError:
        logger.warning(
            "Password reset requested but email isn't configured (set EMAIL_PROVIDER and "
            "its credentials). No email was sent."
        )
    except EmailSendError as exc:
        logger.error("Password reset email failed: %s", exc)
