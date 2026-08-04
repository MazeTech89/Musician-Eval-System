"""Email helpers for verification and password reset."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def _is_email_configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_from)


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send a simple email if SMTP is configured."""
    if not _is_email_configured():
        logger.info("SMTP not configured; skipping email delivery to %s", to_email)
        return False

    message = EmailMessage()
    message["From"] = settings.smtp_from or "no-reply@example.com"
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port or 587) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
        return True
    except Exception as exc:  # pragma: no cover - network dependent
        logger.exception("Failed to send email to %s", to_email)
        raise RuntimeError("Unable to send email") from exc


def send_verification_email(to_email: str, verification_url: str) -> bool:
    body = (
        "Please verify your email address by visiting the link below:\n\n"
        f"{verification_url}\n"
    )
    return send_email(to_email, "Verify your email address", body)


def send_password_reset_email(to_email: str, reset_url: str) -> bool:
    body = (
        "You requested a password reset. Use the link below to create a new password:\n\n"
        f"{reset_url}\n"
    )
    return send_email(to_email, "Reset your password", body)
