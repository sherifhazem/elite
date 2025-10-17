"""Offer CRUD blueprint providing JSON endpoints."""

from datetime import datetime

from flask import Blueprint, jsonify, request

from app import db
from app.models.company import Company
from app.models.offer import Offer


offer_routes = Blueprint("offer_routes", __name__)


def _serialize_offer(offer: Offer) -> dict:
    """Return a dictionary representation of an offer."""

    return {
        "id": offer.id,
        "title": offer.title,
        "discount_percent": offer.discount_percent,
        "valid_until": offer.valid_until.isoformat() if offer.valid_until else None,
        "company_id": offer.company_id,
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


@offer_routes.route("/", methods=["GET"])
def list_offers():
    """Return all offers provided by registered companies."""

    offers = Offer.query.order_by(Offer.id).all()
    return jsonify([_serialize_offer(offer) for offer in offers]), 200


@offer_routes.route("/", methods=["POST"])
def create_offer():
    """Create a new offer from the provided JSON payload."""

    payload = request.get_json(silent=True) or {}
    title = payload.get("title")
    discount_percent = payload.get("discount_percent")
    company_id = payload.get("company_id")
    valid_until_raw = payload.get("valid_until")

    if title is None or discount_percent is None or company_id is None:
        return jsonify({"error": "title, discount_percent, and company_id are required."}), 400

    try:
        discount_percent = float(discount_percent)
    except (TypeError, ValueError):
        return jsonify({"error": "discount_percent must be a number."}), 400

    if not Company.query.get(company_id):
        return jsonify({"error": "Associated company not found."}), 404

    valid_until = _parse_datetime(valid_until_raw)
    if valid_until_raw and valid_until is None:
        return jsonify({"error": "valid_until must be in ISO 8601 format."}), 400

    offer = Offer(
        title=title,
        discount_percent=discount_percent,
        company_id=company_id,
        valid_until=valid_until,
    )
    db.session.add(offer)
    db.session.commit()
    return jsonify(_serialize_offer(offer)), 201


@offer_routes.route("/<int:offer_id>", methods=["PUT"])
def update_offer(offer_id: int):
    """Update an existing offer identified by offer_id."""

    offer = Offer.query.get(offer_id)
    if offer is None:
        return jsonify({"error": "Offer not found."}), 404

    payload = request.get_json(silent=True) or {}

    if "title" in payload:
        offer.title = payload["title"]

    if "discount_percent" in payload:
        try:
            offer.discount_percent = float(payload["discount_percent"])
        except (TypeError, ValueError):
            return jsonify({"error": "discount_percent must be a number."}), 400

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
    return jsonify(_serialize_offer(offer)), 200


@offer_routes.route("/<int:offer_id>", methods=["DELETE"])
def delete_offer(offer_id: int):
    """Remove an offer from the database."""

    offer = Offer.query.get(offer_id)
    if offer is None:
        return jsonify({"error": "Offer not found."}), 404

    db.session.delete(offer)
    db.session.commit()
    return jsonify({"status": "deleted"}), 200


__all__ = ["offer_routes"]
