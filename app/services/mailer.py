# LINKED: Registration Flow & Welcome Notification Review (Users & Companies)
# Verified welcome email and internal notification triggers for new accounts.
"""Utility helpers for composing and sending transactional emails via Flask-Mail."""

from __future__ import annotations

from typing import Any, Dict, Optional

from flask import current_app, render_template
from flask_mail import Message

from app import mail

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


def safe_send(msg: Message) -> bool:
    """Safely send an email message."""

    try:
        mail.send(msg)
    except Exception:  # pragma: no cover - mail transport guard
        return False

    return True


def _company_primary_email(company) -> str:
    """Return the most suitable email address for company correspondence."""

    if company is None:
        return ""

    owner = getattr(company, "owner", None)
    owner_email = getattr(owner, "email", "") if owner else ""
    if owner_email:
        return owner_email

    preferences = getattr(company, "notification_preferences", None) or {}
    if isinstance(preferences, dict):
        contact_email = preferences.get("contact_email") or preferences.get("email")
        if contact_email:
            return contact_email

    return ""


def _dispatch_email(recipient: str, subject: str, html_body: str) -> bool:
    """Send an HTML email using the configured SMTP settings."""

    msg = Message(subject, recipients=[recipient])
    msg.sender = current_app.config.get("MAIL_DEFAULT_SENDER")
    msg.html = html_body
    return safe_send(msg)


def _send_company_status_email(company, subject: str, html_body: str) -> bool:
    """Deliver a simple HTML email to the primary company contact."""

    recipient = _company_primary_email(company)
    if not recipient:
        return False

    if current_app.config.get("MAIL_SUPPRESS_SEND", False):
        return True

    if not _dispatch_email(recipient, subject, html_body):
        return False

    return True


def send_email(
    recipient: str,
    subject: str,
    template: str,
    context: Optional[Dict[str, Any]] = None,
) -> bool:
    """Render an email template and deliver it to the provided recipient."""

    if not recipient:
        return False

    safe_context = dict(context or {})

    html_body = render_template(template, **safe_context)

    if current_app.config.get("MAIL_SUPPRESS_SEND", False):
        return True

    if not _dispatch_email(recipient, subject, html_body):
        return False

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


def send_company_approval_email(company) -> bool:
    """Notify the company contact when the application has been approved."""

    company_name = getattr(company, "name", "Valued Partner") or "Valued Partner"
    html_body = (
        f"<p>Hello {company_name},</p>"
        "<p>Your company application has been approved. You can now sign in to manage your offers and engage with ELITE members.</p>"
        "<p>Best regards,<br>The ELITE Team</p>"
    )
    return _send_company_status_email(
        company,
        "Your Company Application Has Been Approved",
        html_body,
    )


def send_company_correction_email(company, notes, link: str) -> bool:
    """Send a correction email including review notes and the re-submission link."""

    company_name = getattr(company, "name", "Valued Partner") or "Valued Partner"
    safe_notes = notes or "Please review the requested changes and submit the corrected information."
    html_body = (
        f"<p>Hello {company_name},</p>"
        f"<p>We reviewed your application and need a few updates before approval:</p>"
        f"<blockquote>{safe_notes}</blockquote>"
        f"<p>You can update your details here: <a href=\"{link}\">Complete your company registration</a>.</p>"
        "<p>Thank you for your cooperation,<br>The ELITE Team</p>"
    )
    return _send_company_status_email(
        company,
        "Action Required: Update Your Company Application",
        html_body,
    )


def send_company_suspension_email(company) -> bool:
    """Inform the company contact that their account has been suspended."""

    company_name = getattr(company, "name", "Valued Partner") or "Valued Partner"
    html_body = (
        f"<p>Hello {company_name},</p>"
        "<p>We have temporarily suspended your company account. Please contact the ELITE support team if you have any questions or would like to appeal the decision.</p>"
        "<p>Sincerely,<br>The ELITE Team</p>"
    )
    return _send_company_status_email(
        company,
        "Notice: Your Company Account Has Been Suspended",
        html_body,
    )


def send_company_reactivation_email(company) -> bool:
    """Let the company know their account has been restored."""

    company_name = getattr(company, "name", "Valued Partner") or "Valued Partner"
    html_body = (
        f"<p>Hello {company_name},</p>"
        "<p>Your company account has been reactivated. You can sign in again to manage offers and review performance analytics.</p>"
        "<p>Welcome back,<br>The ELITE Team</p>"
    )
    return _send_company_status_email(
        company,
        "Good News: Your Company Account Is Active Again",
        html_body,
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


def _resolve_company_recipient(company) -> str:
    """Return the best email address to reach a company contact."""

    if company is None:
        return ""

    direct_email = getattr(company, "email", "")
    if direct_email:
        return direct_email

    owner = getattr(company, "owner", None)
    owner_email = getattr(owner, "email", "") if owner else ""
    if owner_email:
        return owner_email

    preferences = getattr(company, "notification_preferences", None) or {}
    if isinstance(preferences, dict):
        contact_email = preferences.get("contact_email") or preferences.get("email")
        if contact_email:
            return contact_email

    return ""


def send_company_approval_email(company) -> bool:
    """Send a confirmation email when a company application is approved."""

    recipient = _resolve_company_recipient(company)
    if not recipient:
        return False

    company_name = getattr(company, "name", "") or "your company"
    base_url = (flask_app.config.get("BASE_URL") or "").rstrip("/")
    login_link = f"{base_url}/company/login" if base_url else "/company/login"
    html_body = f"""
    <h3>Welcome to Elite Discounts!</h3>
    <p>Dear {company_name},</p>
    <p>Your registration has been approved. You can now access your portal to upload offers and manage QR codes.</p>
    <p><a href="{login_link}">Click here to log in</a></p>
    """

    with flask_app.app_context():
        if not _dispatch_email(
            recipient,
            "Your Company Has Been Approved - Elite Program",
            html_body,
        ):
            return False
    return True


def send_company_correction_email(company, notes: str, correction_link: str) -> bool:
    """Send a correction request email with admin notes and update link."""

    recipient = _resolve_company_recipient(company)
    if not recipient:
        return False

    company_name = getattr(company, "name", "") or "your company"
    safe_notes = notes or ""
    html_body = f"""
    <h3>Elite Discounts - Application Review</h3>
    <p>Dear {company_name},</p>
    <p>Your application needs some corrections or additional details before approval.</p>
    <p><b>Admin Notes:</b> {safe_notes}</p>
    <p>Please visit the following link to update your information:</p>
    <p><a href="{correction_link}">{correction_link}</a></p>
    """

    with flask_app.app_context():
        if not _dispatch_email(
            recipient,
            "Correction Required for Your Company Application",
            html_body,
        ):
            return False
    return True


def send_company_suspension_email(company) -> bool:
    """Notify a company contact that their account has been suspended."""

    recipient = _resolve_company_recipient(company)
    if not recipient:
        return False

    company_name = getattr(company, "name", "") or "your company"
    html_body = f"""
    <h3>Notice of Suspension</h3>
    <p>Dear {company_name},</p>
    <p>Your company account has been temporarily suspended due to policy violations or pending review.</p>
    <p>If you believe this is a mistake, please contact our support team.</p>
    """

    with flask_app.app_context():
        if not _dispatch_email(
            recipient,
            "Your Account Has Been Suspended - Elite Discounts",
            html_body,
        ):
            return False
    return True


def send_company_reactivation_email(company) -> bool:
    """Notify a company contact that their portal access has been restored."""

    recipient = _resolve_company_recipient(company)
    if not recipient:
        return False

    company_name = getattr(company, "name", "") or "your company"
    base_url = (flask_app.config.get("BASE_URL") or "").rstrip("/")
    login_link = f"{base_url}/company/login" if base_url else "/company/login"
    html_body = f"""
    <h3>Account Reactivated</h3>
    <p>Dear {company_name},</p>
    <p>Your company account has been reactivated. You may now log in to your portal again and continue offering discounts.</p>
    <p><a href="{login_link}">Login to your account</a></p>
    """

    with flask_app.app_context():
        if not _dispatch_email(
            recipient,
            "Your Company Account Has Been Reactivated",
            html_body,
        ):
            return False
    return True


__all__ = [
    "send_email",
    "send_member_welcome_email",
    "send_company_welcome_email",
    "send_staff_welcome_email",
    "send_welcome_email",
    "send_company_approval_email",
    "send_company_correction_email",
    "send_company_suspension_email",
    "send_company_reactivation_email",
    "WELCOME_EMAIL_SUBJECTS",
]
