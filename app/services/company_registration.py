"""Shared business logic for registering companies and notifying admins."""

from __future__ import annotations

import re
from datetime import datetime
from http import HTTPStatus
from typing import Dict, Tuple
from urllib.parse import urlparse

from flask import current_app, url_for
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from .. import db
from ..forms import CITY_CHOICES, INDUSTRY_CHOICES
from ..models.company import Company
from ..models.user import User
from ..services.mailer import send_email
from ..services.notifications import push_admin_notification, queue_notification


def register_company_account(payload: Dict[str, str]) -> Tuple[Dict[str, object], HTTPStatus]:
    """Validate payload data, create company + owner, and notify admins."""

    requested_username = (payload.get("username") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password")
    company_name = (payload.get("company_name") or "").strip()
    description = payload.get("description")
    phone_number = (payload.get("phone_number") or "").strip()
    industry = (payload.get("industry") or "").strip()
    city = (payload.get("city") or "").strip()
    website_url = (payload.get("website_url") or "").strip()
    social_url = (payload.get("social_url") or "").strip()

    if not email or not password or not company_name:
        return (
            {
                "error": "email, password, and company_name are required.",
            },
            HTTPStatus.BAD_REQUEST,
        )

    if not phone_number or len(phone_number) < 8:
        return (
            {"error": "A valid phone_number with at least 8 characters is required."},
            HTTPStatus.BAD_REQUEST,
        )

    allowed_industries = {choice for choice, _ in INDUSTRY_CHOICES if choice}
    allowed_cities = {choice for choice, _ in CITY_CHOICES if choice}
    if industry not in allowed_industries:
        return (
            {"error": "industry is required and must be a supported choice."},
            HTTPStatus.BAD_REQUEST,
        )
    if city not in allowed_cities:
        return (
            {"error": "city is required and must be a supported choice."},
            HTTPStatus.BAD_REQUEST,
        )

    def _is_valid_url(value: str) -> bool:
        if not value:
            return False
        parsed = urlparse(value)
        return bool(parsed.scheme in {"http", "https"} and parsed.netloc)

    if website_url and not _is_valid_url(website_url):
        return (
            {"error": "website_url must be a valid HTTP or HTTPS link."},
            HTTPStatus.BAD_REQUEST,
        )
    if not social_url or not _is_valid_url(social_url):
        return (
            {"error": "social_url must be a valid HTTP or HTTPS link."},
            HTTPStatus.BAD_REQUEST,
        )

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        normalized_role = (existing_user.role or "").strip().lower()
        associated_company_exists = False
        if existing_user.company_id:
            associated_company_exists = (
                Company.query.filter_by(id=existing_user.company_id).first() is not None
            )
        owns_company = (
            Company.query.filter_by(owner_user_id=existing_user.id).first() is not None
        )

        if (
            normalized_role == "company"
            and not associated_company_exists
            and not owns_company
        ):
            current_app.logger.info(
                "Removed orphaned company user before re-registering the company.",
                extra={"email": existing_user.email},
            )
            db.session.delete(existing_user)
            db.session.flush()
        else:
            return (
                {"error": "A user with the provided email already exists."},
                HTTPStatus.BAD_REQUEST,
            )

    if Company.query.filter_by(name=company_name).first():
        return (
            {"error": "A company with the provided name already exists."},
            HTTPStatus.BAD_REQUEST,
        )

    def _generate_username() -> str:
        base_source = requested_username or company_name or email.split("@")[0]
        cleaned = re.sub(r"[^\w\u0621-\u064A]+", "", base_source, flags=re.UNICODE)
        cleaned = cleaned or "company"
        candidate = cleaned
        suffix = 1
        while User.query.filter_by(username=candidate).first():
            candidate = f"{cleaned}{suffix}"
            suffix += 1
        return candidate

    username = requested_username or _generate_username()

    if requested_username and User.query.filter_by(username=username).first():
        return (
            {"error": "A user with the provided username already exists."},
            HTTPStatus.BAD_REQUEST,
        )

    company = Company(name=company_name, description=description)
    company.set_status("pending")
    company.admin_notes = None

    owner = User(username=username, email=email)
    owner.set_password(password)
    owner.role = "company"
    owner.membership_level = "Basic"
    owner.is_active = False

    company.owner = owner
    owner.company = company
    company.notification_preferences = {
        "contact_phone": phone_number,
        "industry": industry,
        "city": city,
        "website_url": website_url or None,
        "social_url": social_url,
        "submitted_at": datetime.utcnow().isoformat() + "Z",
    }

    db.session.add(owner)
    db.session.add(company)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return (
            {"error": "Unable to register company with the provided details."},
            HTTPStatus.BAD_REQUEST,
        )

    push_admin_notification(
        event_type="company.new_application",
        title="New Company Application",
        message=f"A new company '{company.name}' submitted an application.",
        link="/admin/companies?status=pending",
        company_id=company.id,
        actor_id=getattr(current_user, "id", None),
    )

    notify_admin_of_company_request(
        company=company,
        owner=owner,
        phone_number=phone_number,
        industry=industry,
        city=city,
    )

    response = {
        "company": {
            "id": company.id,
            "name": company.name,
            "description": company.description,
            "created_at": company.created_at.isoformat() if company.created_at else None,
            "status": company.status,
            "admin_notes": company.admin_notes,
        },
        "owner": {
            "id": owner.id,
            "username": owner.username,
            "email": owner.email,
            "role": owner.role,
            "is_active": owner.is_active,
        },
        "message": "Company registration request received and pending review.",
        "redirect_url": url_for("auth.login_page"),
    }
    return response, HTTPStatus.CREATED


def notify_admin_of_company_request(
    *,
    company: Company,
    owner: User,
    phone_number: str,
    industry: str,
    city: str,
) -> None:
    """Send admin notifications and email summarizing the company request."""

    admin_users = (
        User.query.filter(
            User.role.in_(["admin", "superadmin"]),
            User.is_active.is_(True),
        )
        .order_by(User.id)
        .all()
    )

    if not admin_users:
        current_app.logger.warning(
            "Company registration pending but no admin recipients found.",
            extra={"company_id": company.id},
        )
    else:
        message = (
            f"تم استلام طلب تسجيل شركة جديدة: {company.name}.\n"
            f"المدينة: {city}.\n"
            f"المجال: {industry}.\n"
            f"رقم التواصل: {phone_number}."
        )
        metadata = {
            "company_id": company.id,
            "company_name": company.name,
            "industry": industry,
            "city": city,
            "phone_number": phone_number,
            "owner_id": owner.id,
            "owner_email": owner.email,
        }
        for admin in admin_users:
            queue_notification(
                admin.id,
                type="new_company_request",
                title="طلب تسجيل شركة جديد",
                message=message,
                metadata=metadata,
            )

    admin_email = (
        current_app.config.get("ADMIN_CONTACT_EMAIL")
        or current_app.config.get("MAIL_DEFAULT_SENDER")
        or current_app.config.get("MAIL_USERNAME")
    )
    if not admin_email:
        return

    subject = f"طلب تسجيل شركة جديد: {company.name}"
    message_lines = [
        f"اسم الشركة: {company.name}",
        f"المدينة: {city}",
        f"المجال: {industry}",
        f"البريد المسؤول: {owner.email}",
        f"رقم الجوال: {phone_number}",
        f"رابط التواصل: {company.notification_preferences.get('social_url')}",
    ]
    if company.notification_preferences.get("website_url"):
        message_lines.append(
            f"الموقع الإلكتروني: {company.notification_preferences.get('website_url')}"
        )
    message_lines.append("الحالة الحالية: Pending Review")

    message_html = "<br>".join(message_lines)
    context = {"subject": subject, "message_html": message_html}
    send_email(admin_email, subject, "emails/admin_broadcast.html", context)


__all__ = ["register_company_account", "notify_admin_of_company_request"]
