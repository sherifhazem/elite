"""Utility helpers for composing and sending transactional emails via Flask-Mail."""

from flask import current_app
from flask_mail import Mail, Message

from app import app

# Initialize a Mail instance tied to the core Flask app configuration so SMTP
# credentials configured in ``Config`` are honored for every outgoing message.
mail = Mail(app)


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
