# LINKED: Registration Flow & Welcome Notification Review (Users & Companies)
# Verified welcome email and internal notification triggers for new accounts.
"""Administrative email helpers for the communication center."""

from __future__ import annotations

from html import escape
from typing import Iterable, Optional, Sequence

from flask import current_app

from .mailer import send_email


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

    if current_app.config.get("MAIL_SUPPRESS_SEND"):
        return len(recipient_list)

    delivered = 0
    for email in recipient_list:
        try:
            send_email(
                email,
                safe_subject,
                "core/emails/admin_broadcast.html",
                {"subject": safe_subject, "message_html": html_body},
            )
        except Exception:  # pragma: no cover - mail transport guard
            continue
        delivered += 1

    return delivered


__all__ = ["send_admin_broadcast_email"]
