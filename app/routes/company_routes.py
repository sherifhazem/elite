"""Company CRUD blueprint providing JSON endpoints."""

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from .. import db
from ..models.company import Company
from ..models.user import User
from ..services.notifications import ensure_welcome_notification
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
    db.session.add(company)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Company with the same name already exists."}), 400

    if company.owner:
        ensure_welcome_notification(company.owner, context="company")

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
