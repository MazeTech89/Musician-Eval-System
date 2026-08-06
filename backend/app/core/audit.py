"""Security audit logging and alert helpers."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from app.core.config import settings
from app.core.email import send_email

logger = logging.getLogger("app.audit")


def _serialize_details(details: dict[str, Any]) -> str:
    # JSON (not str-formatting) so log entries stay machine-parseable for later log analysis/SIEM.
    payload = {"timestamp": datetime.now(UTC).isoformat(), **details}
    return json.dumps(payload, sort_keys=True, default=str)


def record_audit_event(event: str, **details: Any) -> None:
    """Write a structured audit log entry."""
    # info level: routine/expected events (e.g. successful login, resource created).
    logger.info("%s %s", event, _serialize_details(details))


def record_security_alert(event: str, **details: Any) -> None:
    """Write a security alert and notify the configured recipient if present."""
    # warning level: anomalous/suspicious events (rate limiting, lockouts) worth a human's attention.
    message = _serialize_details({"event": event, **details})
    logger.warning("%s", message)

    if not settings.security_alert_email:
        # No recipient configured: log-only, don't attempt to send email.
        return

    try:
        sent = send_email(
            settings.security_alert_email,
            f"[{settings.app_name}] Security alert: {event}",
            message,
        )
    except RuntimeError:
        # Email delivery failure must never break the caller's request flow (e.g. login);
        # the event is already durably logged above regardless of email outcome.
        logger.exception("Failed to deliver security alert email")
        return

    if not sent:
        logger.warning("Security alert email skipped because SMTP is not configured")
