# LINKED: Registration Flow & Welcome Notification Review (Users & Companies)
# Verified welcome email and internal notification triggers for new accounts.
"""Utility helpers for composing and sending transactional emails via Flask-Mail."""

from __future__ import annotations

from typing import Any, Dict, Optional

from flask import current_app, render_template
from flask_mail import Mail, Message

from app import app

# Initialize a Mail instance tied to the core Flask app configuration so SMTP
# credentials configured in ``Config`` are honored for every outgoing message.
mail = Mail(app)

WELCOME_EMAIL_SUBJECTS: Dict[str, str] = {
    "member": "مرحبًا بك في ELITE – عروضك المميزة بانتظارك!",
    "company": "مرحبًا بكم في ELITE – استعدوا لتوسيع قاعدة عملائكم!",
    "staff": "👋 مرحبًا بك في فريق ELITE الإداري!",
}

WELCOME_EMAIL_TEMPLATES: Dict[str, str] = {
    "member": "emails/welcome_user.html",
    "company": "emails/welcome_company.html",
    "staff": "emails/welcome_staff.html",
}


def _dispatch_email(recipient: str, subject: str, html_body: str) -> None:
    """Send an HTML email using the configured SMTP settings."""

    msg = Message(subject, recipients=[recipient])
    msg.sender = current_app.config.get("MAIL_DEFAULT_SENDER")
    msg.html = html_body
    mail.send(msg)


def send_email(
    recipient: str,
    subject: str,
    template: str,
    context: Optional[Dict[str, Any]] = None,
) -> bool:
    """Render an email template and deliver it to the provided recipient."""

    if not recipient:
        current_app.logger.warning("Skipping email send due to missing recipient")
        return False

    safe_context = dict(context or {})

    with app.app_context():
        html_body = render_template(template, **safe_context)

        if current_app.config.get("MAIL_SUPPRESS_SEND", False):
            current_app.logger.info(
                "Email suppressed by configuration",
                extra={"recipient": recipient, "subject": subject},
            )
            current_app.logger.debug(
                "Suppressed email subject='%s' template='%s' context=%s",
                subject,
                template,
                safe_context,
            )
            return True

        try:
            _dispatch_email(recipient, subject, html_body)
        except Exception as error:  # pragma: no cover - mail transport guard
            current_app.logger.exception("Email delivery failed: %s", error)
            return False

    current_app.logger.info(
        "Email delivered successfully",
        extra={"recipient": recipient, "subject": subject},
    )
    return True


def send_member_welcome_email(*, user) -> bool:
    """Send the standardized welcome email to a newly registered member."""

    if user is None:
        return False

    context = {
        "recipient_name": getattr(user, "username", "").strip() or user.email,
        "welcome_message": (
            "مرحبًا بكم في عائلة ELITE!\n"
            "استمتع بالعروض المميزة والخصومات المخصصة لمستواك منذ لحظة تسجيلك."
        ),
    }
    return send_email(
        getattr(user, "email", ""),
        WELCOME_EMAIL_SUBJECTS["member"],
        WELCOME_EMAIL_TEMPLATES["member"],
        context,
    )


def send_company_welcome_email(*, owner, company_name: str) -> bool:
    """Send the standardized welcome email to a newly registered company owner."""

    if owner is None:
        return False

    context = {
        "recipient_name": getattr(owner, "username", "").strip() or owner.email,
        "company_name": company_name,
        "welcome_message": (
            "مرحبًا بكم في منصة ELITE للشركات!\n"
            "يمكنكم الآن إدارة عروضكم ومتابعة تفاعلات الأعضاء بسهولة من لوحة التحكم الخاصة بكم."
        ),
    }
    return send_email(
        getattr(owner, "email", ""),
        WELCOME_EMAIL_SUBJECTS["company"],
        WELCOME_EMAIL_TEMPLATES["company"],
        context,
    )


def send_staff_welcome_email(*, user) -> bool:
    """Send the welcome email reserved for administrative staff accounts."""

    if user is None:
        return False

    context = {
        "recipient_name": getattr(user, "username", "").strip() or user.email,
        "welcome_message": (
            "مرحبًا بك ضمن فريق ELITE الإداري!\n"
            "يمكنك الآن تسجيل الدخول والبدء في إدارة مهامك اليومية بكل سهولة."
        ),
    }
    return send_email(
        getattr(user, "email", ""),
        WELCOME_EMAIL_SUBJECTS["staff"],
        WELCOME_EMAIL_TEMPLATES["staff"],
        context,
    )


def send_welcome_email(
    *,
    user,
    template_key: str,
    company_name: Optional[str] = None,
) -> bool:
    """Backward-compatible helper delegating to role-specific welcome emails."""

    normalized_key = (template_key or "member").strip().lower()
    if normalized_key == "company":
        resolved_company = company_name or getattr(
            getattr(user, "company", None),
            "name",
            "",
        )
        return send_company_welcome_email(owner=user, company_name=resolved_company)
    if normalized_key in {"admin", "superadmin", "staff"}:
        return send_staff_welcome_email(user=user)
    return send_member_welcome_email(user=user)


__all__ = [
    "send_email",
    "send_member_welcome_email",
    "send_company_welcome_email",
    "send_staff_welcome_email",
    "send_welcome_email",
    "WELCOME_EMAIL_SUBJECTS",
]
