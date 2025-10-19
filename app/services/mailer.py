"""Utility helpers for composing and sending transactional emails via Flask-Mail."""

from __future__ import annotations

from typing import Dict, Optional

from flask import current_app
from flask_mail import Mail, Message

from app import app
from app.models.notification import Notification
from app.models.user import User

# Initialize a Mail instance tied to the core Flask app configuration so SMTP
# credentials configured in ``Config`` are honored for every outgoing message.
mail = Mail(app)

# ADDED: Automated welcome email delivery for new users, companies, and staff.

WELCOME_EMAIL_TEMPLATES: Dict[str, Dict[str, str]] = {
    "member": {
        "subject": "🎉 أهلاً بك في برنامج ELITE!",
        "body": (
            "<p>مرحبًا {username},</p>"
            "<p>يسعدنا انضمامك إلى مجتمع ELITE المميز.</p>"
            "<p>يمكنك الآن الاستفادة من العروض الحصرية والخصومات المتاحة عبر حسابك.</p>"
            "<p>نرحب بك مجددًا،<br>فريق ELITE.</p>"
        ),
    },
    "company": {
        "subject": "🤝 مرحبًا بشركائنا الجدد في ELITE!",
        "body": (
            "<p>مرحبًا {company_name},</p>"
            "<p>شكرًا لانضمامكم إلى منصة ELITE.</p>"
            "<p>يمكنكم الآن إضافة عروضكم الخاصة وجذب المزيد من العملاء من خلال بوابتكم المخصصة.</p>"
            "<p>نتمنى لكم نجاحًا مستمرًا،<br>فريق ELITE.</p>"
        ),
    },
    "staff": {
        "subject": "👋 مرحبًا بك في فريق ELITE الإداري!",
        "body": (
            "<p>مرحبًا {username},</p>"
            "<p>تم إنشاء حسابك بنجاح ضمن فريق ELITE.</p>"
            "<p>يمكنك الآن تسجيل الدخول وبدء العمل على إدارة المهام الموكلة إليك.</p>"
            "<p>بالتوفيق،<br>إدارة ELITE.</p>"
        ),
    },
}


def send_email(to: str, subject: str, html_body: str) -> None:
    """Send an HTML email using the configured SMTP settings."""

    # Push an application context to ensure Flask-Mail can read configuration
    # values (server, port, credentials) when running from background tasks.
    with app.app_context():
        # Compose the email message with explicit HTML body content.
        msg = Message(subject, recipients=[to])
        msg.sender = current_app.config.get("MAIL_DEFAULT_SENDER")
        msg.html = html_body
        # Dispatch the email through the SMTP server defined in ``Config``.
        mail.send(msg)


def _welcome_notification_exists(user: User, context_key: str) -> bool:
    """Return True when a matching welcome notification already exists."""

    if user is None or not getattr(user, "id", None):
        return False

    notifications = Notification.query.filter_by(
        user_id=user.id,
        type="welcome_message",
    ).all()
    for notification in notifications:
        metadata = notification.metadata_json or {}
        existing_context = (metadata.get("welcome_context") or "").strip().lower()
        if existing_context == context_key:
            return True
    return False


def send_welcome_email(
    *,
    user: Optional[User],
    template_key: str,
    email: Optional[str] = None,
    company_name: Optional[str] = None,
) -> bool:
    """Render and dispatch the appropriate welcome email when allowed."""

    normalized_key = (template_key or "member").strip().lower()
    template = WELCOME_EMAIL_TEMPLATES.get(normalized_key)
    if not template:
        current_app.logger.warning(
            "Unknown welcome email template key '%s'", normalized_key
        )
        return False

    recipient_email = (email or getattr(user, "email", "") or "").strip()
    if not recipient_email:
        current_app.logger.warning("Skipping welcome email: missing recipient address")
        return False

    if user and _welcome_notification_exists(user, normalized_key):
        current_app.logger.info(
            "Skipping welcome email for %s because a welcome notification already exists",
            recipient_email,
        )
        return False

    context = {
        "username": getattr(user, "username", "").strip() or recipient_email,
        "company_name": (company_name or getattr(user, "username", "")).strip()
        or recipient_email,
    }

    subject = template["subject"]
    html_body = template["body"].format(**context)

    if current_app.config.get("MAIL_SUPPRESS_SEND", False):
        current_app.logger.info(
            "Welcome email suppressed by configuration for %s", recipient_email
        )
        current_app.logger.debug("Subject: %s | Body: %s", subject, html_body)
        return True

    try:
        send_email(recipient_email, subject, html_body)
    except Exception as error:  # pragma: no cover - mail transport guard
        current_app.logger.exception("Email delivery failed: %s", error)
        return False

    current_app.logger.info("Welcome email sent successfully to %s", recipient_email)
    return True
