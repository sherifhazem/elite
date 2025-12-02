# LINKED: Fixed duplicate email error after company deletion
# Ensures orphaned company owners are cleaned up before new company registration.
# LINKED: Registration Flow & Welcome Notification Review (Users & Companies)
# Verified welcome email and internal notification triggers for new accounts.
"""Company CRUD blueprint providing JSON endpoints."""

# LINKED: Enhanced company registration form (business details + admin review integration)
# Added mandatory fields for phone, industry, city, website, and social links without schema changes.

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from app.core.database import db
from app.models import Company, User
from app.modules.companies.services.company_profile_service import (
    remove_company_owner_accounts,
)
from app.modules.companies.services.company_registration_service import (
    register_company_account,
)
from app.services.mailer import send_company_welcome_email
from app.modules.members.services.member_notifications_service import (
    send_welcome_notification,
)
from app.services.access_control import require_role


companies = Blueprint("companies", __name__)


def _serialize_company(company: Company) -> dict:
    """Return a dictionary representation of a company."""

    return {
        "id": company.id,
        "name": company.name,
        "description": company.description,
        "created_at": company.created_at.isoformat() if company.created_at else None,
        "status": company.status,
        "admin_notes": company.admin_notes,
    }


@companies.route("/register", methods=["POST"], endpoint="register_company")
def register_company():
    """Public endpoint allowing a business to create its company account."""

    payload = {k: v for k, v in (getattr(request, "cleaned", {}) or {}).items() if not k.startswith("__")}
    response, status = register_company_account(payload)
    # Register company account returns serialized owner/company payload already aligned
    # with auth registration flow.
    return jsonify(response), status


@companies.route("/", methods=["GET"], endpoint="list_companies")
def list_companies():
    """Return all companies collaborating with ELITE."""

    companies = Company.query.order_by(Company.id).all()
    return jsonify([_serialize_company(company) for company in companies]), 200


@companies.route("/", methods=["POST"], endpoint="create_company")
@require_role("admin")
def create_company():
    """Create a new company from the provided JSON payload."""

    payload = {k: v for k, v in (getattr(request, "cleaned", {}) or {}).items() if not k.startswith("__")}
    name = payload.get("name")
    description = payload.get("description")

    if not name:
        return jsonify({"error": "name is required."}), 400

    company = Company(name=name, description=description)
    company.status = "pending"

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


@companies.route(
    "/<int:company_id>", methods=["PUT"], endpoint="update_company"
)
@require_role("admin")
def update_company(company_id: int):
    """Update the company identified by company_id."""

    company = Company.query.get(company_id)
    if company is None:
        return jsonify({"error": "Company not found."}), 404

    payload = {k: v for k, v in (getattr(request, "cleaned", {}) or {}).items() if not k.startswith("__")}
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


@companies.route(
    "/<int:company_id>", methods=["DELETE"], endpoint="delete_company"
)
@require_role("admin")
def delete_company(company_id: int):
    """Remove a company from the database."""

    company = Company.query.get(company_id)
    if company is None:
        return jsonify({"error": "Company not found."}), 404

    remove_company_owner_accounts(company)
    db.session.delete(company)
    db.session.commit()
    return jsonify({"status": "deleted"}), 200


__all__ = ["companies"]
