# LINKED: Registration Flow & Welcome Notification Review (Users & Companies)
# Verified welcome email and internal notification triggers for new accounts.
"""Administrative email helpers for the communication center."""

from __future__ import annotations

from html import escape
from typing import Iterable, Optional, Sequence

from flask import current_app

from .mailer import send_email
from core.observability.logger import (
    get_service_logger,
    log_service_error,
    log_service_start,
    log_service_step,
    log_service_success,
)


def _normalize_recipients(recipients: Iterable[str]) -> Sequence[str]:
    """Return a list of unique, sanitized recipient email addresses."""

    unique = []
    seen = set()
    for email in recipients or []:
        if not email:
            continue
        normalized = email.strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique.append(normalized)
    return unique


service_logger = get_service_logger(__name__)


def _log(
    function: str,
    event: str,
    message: str,
    details: Optional[dict] = None,
    level: str = "INFO",
) -> None:
    """Emit standardized logs for the email service layer."""

    normalized_level = level.upper()
    if normalized_level == "ERROR" or event in {"service_error", "validation_failure"}:
        log_service_error(__name__, function, message, details=details, event=event)
    elif event == "service_start":
        log_service_start(__name__, function, message, details)
    elif event in {"service_complete", "service_success"}:
        log_service_success(__name__, function, message, details=details, event=event)
    else:
        log_service_step(
            __name__,
            function,
            message,
            details=details,
            event=event,
            level=level,
        )


def send_admin_broadcast_email(
    recipients: Iterable[str],
    *,
    subject: str,
    body: str,
    sender: Optional[object] = None,
) -> int:
    """Send broadcast emails using the configured transactional mailer."""

    recipient_list = _normalize_recipients(recipients)
    if not recipient_list:
        return 0

    safe_subject = (subject or "").strip()
    safe_body = escape(body or "")
    html_body = safe_body.replace("\n", "<br>")

    metadata = {
        "subject": safe_subject,
        "recipient_count": len(recipient_list),
        "sent_by": getattr(sender, "id", None),
    }

    if current_app.config.get("MAIL_SUPPRESS_SEND"):
        _log(
            "send_admin_broadcast_email",
            "service_checkpoint",
            "Broadcast email suppressed",
            metadata,
        )
        return len(recipient_list)

    delivered = 0
    for email in recipient_list:
        try:
            send_email(
                email,
                safe_subject,
                "emails/admin_broadcast.html",
                {"subject": safe_subject, "message_html": html_body},
            )
        except Exception:  # pragma: no cover - mail transport guard
            _log(
                "send_admin_broadcast_email",
                "service_error",
                "Failed to send broadcast email",
                {"recipient": email},
                level="ERROR",
            )
            continue
        delivered += 1

    _log(
        "send_admin_broadcast_email",
        "service_success",
        "Broadcast email sent",
        {"delivered": delivered, "subject": safe_subject},
    )
    return delivered


__all__ = ["send_admin_broadcast_email"]
