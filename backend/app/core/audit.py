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
    payload = {"timestamp": datetime.now(UTC).isoformat(), **details}
    return json.dumps(payload, sort_keys=True, default=str)


def record_audit_event(event: str, **details: Any) -> None:
    """Write a structured audit log entry."""
    logger.info("%s %s", event, _serialize_details(details))


def record_security_alert(event: str, **details: Any) -> None:
    """Write a security alert and notify the configured recipient if present."""
    message = _serialize_details({"event": event, **details})
    logger.warning("%s", message)

    if not settings.security_alert_email:
        return

    try:
        sent = send_email(
            settings.security_alert_email,
            f"[{settings.app_name}] Security alert: {event}",
            message,
        )
    except RuntimeError:
        logger.exception("Failed to deliver security alert email")
        return

    if not sent:
        logger.warning("Security alert email skipped because SMTP is not configured")
