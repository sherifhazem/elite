# LINKED: Registration Flow & Welcome Notification Review (Users & Companies)
# Verified welcome email and internal notification triggers for new accounts.
"""Company CRUD blueprint providing JSON endpoints."""

from http import HTTPStatus

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from .. import db
from ..models.company import Company
from ..models.user import User
from ..services.mailer import send_company_welcome_email
from ..services.notifications import send_welcome_notification
from ..services.roles import require_role


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
    username = (payload.get("username") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password")
    company_name = (payload.get("company_name") or "").strip()
    description = payload.get("description")

    if not username or not email or not password or not company_name:
        return (
            jsonify(
                {
                    "error": "username, email, password, and company_name are required.",
                }
            ),
            HTTPStatus.BAD_REQUEST,
        )

    existing_user = (
        User.query.filter((User.username == username) | (User.email == email)).first()
    )
    if existing_user:
        return (
            jsonify({"error": "A user with the provided username or email already exists."}),
            HTTPStatus.BAD_REQUEST,
        )

    if Company.query.filter_by(name=company_name).first():
        return (
            jsonify({"error": "A company with the provided name already exists."}),
            HTTPStatus.BAD_REQUEST,
        )

    owner = User(username=username, email=email)
    owner.set_password(password)
    owner.role = "company"
    owner.membership_level = "Basic"
    owner.is_active = True

    company = Company(name=company_name, description=description)
    company.owner = owner
    owner.company = company
    company.notification_preferences = {}

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

    send_company_welcome_email(owner=owner, company_name=company.name)
    send_welcome_notification(company)

    response = {
        "company": _serialize_company(company),
        "owner": _serialize_owner(owner),
        "message": "Company registered successfully.",
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

    db.session.delete(company)
    db.session.commit()
    return jsonify({"status": "deleted"}), 200


__all__ = ["company_routes"]
