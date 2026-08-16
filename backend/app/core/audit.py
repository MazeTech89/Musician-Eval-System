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
    # Defensive: ensure serialization or logging failures never propagate to callers.
    try:
        payload = _serialize_details(details)
    except Exception:
        # Fallback: try a best-effort conversion of values to strings, then re-serialize.
        try:
            safe = {k: str(v) for k, v in details.items()}
            payload = _serialize_details(safe)
        except Exception:
            # Last-resort: record minimal payload and continue.
            logger.exception("Failed to serialize audit details; emitting minimal audit entry")
            try:
                payload = json.dumps(
                    {"timestamp": datetime.now(UTC).isoformat(), "event": event}, sort_keys=True
                )
            except Exception:
                # If json.dumps somehow fails, fall back to a simple string.
                payload = f"event={event} timestamp={datetime.now(UTC).isoformat()}"

    try:
        logger.info("%s %s", event, payload)
    except Exception:
        # Ensure logging errors are swallowed and reported to the default logger so callers don't fail.
        logging.getLogger("app.audit").exception("Failed to write audit log entry for %s", event)


def record_security_alert(event: str, **details: Any) -> None:
    """Write a security alert and notify the configured recipient if present."""
    # Warning level: anomalous/suspicious events (rate limiting, lockouts) deserve
    # human attention and can be escalated to email when configured.
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
