# LINKED: Fixed duplicate email error after company deletion
# Ensures orphaned company owners are cleaned up before new company registration.
# LINKED: Registration Flow & Welcome Notification Review (Users & Companies)
# Verified welcome email and internal notification triggers for new accounts.
"""Company CRUD blueprint providing JSON endpoints."""

# LINKED: Enhanced company registration form (business details + admin review integration)
# Added mandatory fields for phone, industry, city, website, and social links without schema changes.

import re
from datetime import datetime
from http import HTTPStatus
from urllib.parse import urlparse

from flask import Blueprint, jsonify, request, url_for
from sqlalchemy.exc import IntegrityError

from .. import db
from ..forms import CITY_CHOICES, INDUSTRY_CHOICES
from ..models.company import Company
from ..models.user import User
from ..services.mailer import send_company_welcome_email
from ..services.notifications import send_welcome_notification
from ..services.roles import require_role
from ..auth.routes import _notify_admin_of_company_request


company_routes = Blueprint("company_routes", __name__)


def _serialize_company(company: Company) -> dict:
    """Return a dictionary representation of a company."""

    return {
        "id": company.id,
        "name": company.name,
        "description": company.description,
        "created_at": company.created_at.isoformat() if company.created_at else None,
    }


def _serialize_owner(user: User) -> dict:
    """Return a minimal representation of the company owner."""

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
    }


@company_routes.route("/register", methods=["POST"])
def register_company():
    """Public endpoint allowing a business to create its company account."""

    payload = request.get_json(silent=True) or {}
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
            jsonify(
                {
                    "error": "email, password, and company_name are required.",
                }
            ),
            HTTPStatus.BAD_REQUEST,
        )

    if not phone_number or len(phone_number) < 8:
        return (
            jsonify({"error": "A valid phone_number with at least 8 characters is required."}),
            HTTPStatus.BAD_REQUEST,
        )

    allowed_industries = {choice for choice, _ in INDUSTRY_CHOICES if choice}
    allowed_cities = {choice for choice, _ in CITY_CHOICES if choice}
    if industry not in allowed_industries:
        return (
            jsonify({"error": "industry is required and must be a supported choice."}),
            HTTPStatus.BAD_REQUEST,
        )
    if city not in allowed_cities:
        return (
            jsonify({"error": "city is required and must be a supported choice."}),
            HTTPStatus.BAD_REQUEST,
        )

    def _is_valid_url(value: str) -> bool:
        if not value:
            return False
        parsed = urlparse(value)
        return bool(parsed.scheme in {"http", "https"} and parsed.netloc)

    if website_url and not _is_valid_url(website_url):
        return (
            jsonify({"error": "website_url must be a valid HTTP or HTTPS link."}),
            HTTPStatus.BAD_REQUEST,
        )
    if not social_url or not _is_valid_url(social_url):
        return (
            jsonify({"error": "social_url must be a valid HTTP or HTTPS link."}),
            HTTPStatus.BAD_REQUEST,
        )

    if User.query.filter_by(email=email).first():
        return (
            jsonify({"error": "A user with the provided email already exists."}),
            HTTPStatus.BAD_REQUEST,
        )

    if Company.query.filter_by(name=company_name).first():
        return (
            jsonify({"error": "A company with the provided name already exists."}),
            HTTPStatus.BAD_REQUEST,
        )

    def _generate_username() -> str:
        """Derive a unique username for the company owner when not provided."""

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
            jsonify({"error": "A user with the provided username already exists."}),
            HTTPStatus.BAD_REQUEST,
        )

    owner = User(username=username, email=email)
    owner.set_password(password)
    owner.role = "company"
    owner.membership_level = "Basic"
    owner.is_active = False

    company = Company(name=company_name, description=description)
    company.owner = owner
    owner.company = company
    company.notification_preferences = {
        "contact_phone": phone_number,
        "industry": industry,
        "city": city,
        "website_url": website_url or None,
        "social_url": social_url,
        "status": "Pending Review",
        "submitted_at": datetime.utcnow().isoformat() + "Z",
    }

    db.session.add(owner)
    db.session.add(company)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return (
            jsonify({"error": "Unable to register company with the provided details."}),
            HTTPStatus.BAD_REQUEST,
        )

    _notify_admin_of_company_request(
        company=company,
        owner=owner,
        phone_number=phone_number,
        industry=industry,
        city=city,
    )

    response = {
        "company": _serialize_company(company),
        "owner": _serialize_owner(owner),
        "message": "Company registration request received and pending review.",
        "redirect_url": url_for("auth.login_page"),
    }
    return jsonify(response), HTTPStatus.CREATED


@company_routes.route("/", methods=["GET"])
def list_companies():
    """Return all companies collaborating with ELITE."""

    companies = Company.query.order_by(Company.id).all()
    return jsonify([_serialize_company(company) for company in companies]), 200


@company_routes.route("/", methods=["POST"])
@require_role("admin")
def create_company():
    """Create a new company from the provided JSON payload."""

    payload = request.get_json(silent=True) or {}
    name = payload.get("name")
    description = payload.get("description")

    if not name:
        return jsonify({"error": "name is required."}), 400

    company = Company(name=name, description=description)

    owner_user_id = payload.get("owner_user_id")
    if owner_user_id is not None:
        try:
            owner_id = int(owner_user_id)
        except (TypeError, ValueError):
            owner_id = None
        if owner_id:
            owner = User.query.get(owner_id)
            if owner:
                company.owner = owner
                owner.company = company
    db.session.add(company)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Company with the same name already exists."}), 400

    if company.owner:
        send_company_welcome_email(owner=company.owner, company_name=company.name)
        send_welcome_notification(company)

    return jsonify(_serialize_company(company)), 201


@company_routes.route("/<int:company_id>", methods=["PUT"])
@require_role("admin")
def update_company(company_id: int):
    """Update the company identified by company_id."""

    company = Company.query.get(company_id)
    if company is None:
        return jsonify({"error": "Company not found."}), 404

    payload = request.get_json(silent=True) or {}
    name = payload.get("name")
    description = payload.get("description")

    if name is not None:
        company.name = name
    if description is not None:
        company.description = description

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Company with the same name already exists."}), 400

    return jsonify(_serialize_company(company)), 200


@company_routes.route("/<int:company_id>", methods=["DELETE"])
@require_role("admin")
def delete_company(company_id: int):
    """Remove a company from the database."""

    company = Company.query.get(company_id)
    if company is None:
        return jsonify({"error": "Company not found."}), 404

    company.remove_owner_account()
    db.session.delete(company)
    db.session.commit()
    return jsonify({"status": "deleted"}), 200


__all__ = ["company_routes"]
