# LINKED: Shared Offers & Redemptions Integration (no schema changes)
"""Offer CRUD blueprint providing JSON endpoints."""

from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy.orm import joinedload

from app.core.database import db
from app.models import Company, Offer
from app.modules.members.services.member_notifications_service import (
    broadcast_new_offer,
)
from app.services.access_control import require_role


offers = Blueprint("offers", __name__)


def _serialize_offer(offer: Offer, membership_level: str) -> dict:
    """Return a dictionary representation of an offer."""

    # TODO: Incentives will be calculated based on verified usage.
    dynamic_discount = offer.base_discount
    return {
        "id": offer.id,
        "title": offer.title,
        "description": offer.description or "",
        "base_discount": offer.base_discount,
        "discount_percent": dynamic_discount,
        "valid_until": offer.valid_until.isoformat() if offer.valid_until else None,
        "image_url": offer.image_url or "",
        "company_id": offer.company_id,
        "company": offer.company.name if offer.company else None,
        "company_summary": (offer.company.description or "")[:140] if offer.company else "",
        "company_description": (offer.company.description or "") if offer.company else "",
        "company_logo_url": offer.company.logo_url if offer.company else "",
        "industry_icon": offer.company.industry_icon if offer.company else None,
        "classification_values": offer.classification_values,
        "created_at": offer.created_at.isoformat() if offer.created_at else None,
    }


def _parse_datetime(value):
    """Return a datetime parsed from ISO 8601 string or None when invalid."""

    if value in (None, ""):
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


@offers.route("/", methods=["GET"], endpoint="list_offers")
def list_offers():
    """Return all offers provided by registered companies."""

    # TODO: Incentives will be calculated based on verified usage.
    membership_level = ""

    offers = Offer.query.options(joinedload(Offer.company)).order_by(Offer.id).all()
    return jsonify([_serialize_offer(offer, membership_level) for offer in offers]), 200


@offers.route("/", methods=["POST"], endpoint="create_offer")
@require_role("admin")
def create_offer():
    """Create a new offer from the provided JSON payload."""

    payload = {k: v for k, v in (getattr(request, "cleaned", {}) or {}).items() if not k.startswith("__")}
    title = payload.get("title")
    base_discount = payload.get("base_discount")
    company_id = payload.get("company_id")
    valid_until_raw = payload.get("valid_until")

    if title is None or company_id is None:
        return jsonify({"error": "title and company_id are required."}), 400

    if base_discount is None:
        # Apply the model default when the client omits the base discount field.
        base_discount_value = 5.0
    else:
        try:
            base_discount_value = float(base_discount)
        except (TypeError, ValueError):
            return jsonify({"error": "base_discount must be a number."}), 400

    if not Company.query.get(company_id):
        return jsonify({"error": "Associated company not found."}), 404

    valid_until = _parse_datetime(valid_until_raw)
    if valid_until_raw and valid_until is None:
        return jsonify({"error": "valid_until must be in ISO 8601 format."}), 400

    offer = Offer(
        title=title,
        base_discount=base_discount_value,
        company_id=company_id,
        valid_until=valid_until,
    )
    db.session.add(offer)
    db.session.commit()
    broadcast_new_offer(offer.id)
    # Return the serialized offer using the baseline Basic tier for consistency.
    return jsonify(_serialize_offer(offer, "Basic")), 201


@offers.route("/<int:offer_id>", methods=["PUT"], endpoint="update_offer")
@require_role("admin")
def update_offer(offer_id: int):
    """Update an existing offer identified by offer_id."""

    offer = Offer.query.get(offer_id)
    if offer is None:
        return jsonify({"error": "Offer not found."}), 404

    payload = {k: v for k, v in (getattr(request, "cleaned", {}) or {}).items() if not k.startswith("__")}

    if "title" in payload:
        offer.title = payload["title"]

    base_discount_updated = False
    if "base_discount" in payload:
        try:
            new_base_discount = float(payload["base_discount"])
        except (TypeError, ValueError):
            return jsonify({"error": "base_discount must be a number."}), 400
        base_discount_updated = new_base_discount != offer.base_discount
        offer.base_discount = new_base_discount

    if "company_id" in payload:
        company_id = payload["company_id"]
        if not Company.query.get(company_id):
            return jsonify({"error": "Associated company not found."}), 404
        offer.company_id = company_id

    if "valid_until" in payload:
        valid_until = _parse_datetime(payload["valid_until"])
        if payload["valid_until"] and valid_until is None:
            return jsonify({"error": "valid_until must be in ISO 8601 format."}), 400
        offer.valid_until = valid_until

    db.session.commit()
    if base_discount_updated:
        broadcast_new_offer(offer.id)
    # Respond with the updated payload using the base membership tier view.
    return jsonify(_serialize_offer(offer, "Basic")), 200


@offers.route("/<int:offer_id>", methods=["DELETE"], endpoint="delete_offer")
@require_role("admin")
def delete_offer(offer_id: int):
    """Remove an offer from the database."""

    offer = Offer.query.get(offer_id)
    if offer is None:
        return jsonify({"error": "Offer not found."}), 404

    db.session.delete(offer)
    db.session.commit()
    return jsonify({"status": "deleted"}), 200


__all__ = ["offers"]
