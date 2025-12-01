"""Offer management routes for the company portal."""

from __future__ import annotations

from datetime import datetime
from http import HTTPStatus
from typing import Dict, Tuple

from flask import flash, jsonify, redirect, render_template, request, url_for

from app.core.database import db
from app.models import Offer
from app.modules.members.services.notifications import (
    broadcast_new_offer,
    fetch_offer_feedback_counts,
)
from app.services.access_control import require_role
from . import company_portal
from app.utils.company_context import _ensure_company, _current_company


def _parse_offer_payload(data: Dict[str, str]) -> Tuple[Dict[str, object], str | None]:
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    base_discount_raw = (data.get("base_discount") or "0").strip()
    valid_until_raw = (data.get("valid_until") or "").strip()
    send_notifications = str(data.get("send_notifications", "")).lower() in {
        "true",
        "1",
        "on",
        "yes",
    }

    if not title:
        return {}, "Title is required."

    try:
        base_discount = float(base_discount_raw)
    except ValueError:
        return {}, "Base discount must be numeric."

    valid_until = None
    if valid_until_raw:
        try:
            valid_until = datetime.strptime(valid_until_raw, "%Y-%m-%d")
        except ValueError:
            return {}, "Valid until must follow YYYY-MM-DD format."

    payload = {
        "title": title,
        "description": description or None,
        "base_discount": base_discount,
        "valid_until": valid_until,
        "send_notifications": send_notifications,
    }
    return payload, None


@company_portal.route("/offers", methods=["GET"], endpoint="list_offers")
@require_role("company")
def list_offers() -> str:
    """Display the offer management table scoped to the current company."""

    company = _current_company()
    offers = (
        Offer.query.filter_by(company_id=company.id)
        .order_by(Offer.created_at.desc())
        .all()
    )
    feedback_totals = fetch_offer_feedback_counts(company.id)
    return render_template(
        "companies/offers.html",
        company=company,
        offers=offers,
        now=datetime.utcnow(),
        feedback_totals=feedback_totals,
    )


@company_portal.route("/offers/new", endpoint="offer_new")
@require_role("company")
def offer_new() -> str:
    """Render the offer creation form used inside the modal component."""

    company = _current_company()
    return render_template(
        "companies/offer_form.html",
        company=company,
        offer=None,
        action_url=url_for("company_portal.offer_create"),
        method="POST",
    )


@company_portal.route("/offers", methods=["POST"], endpoint="offer_create")
@require_role("company")
def offer_create():
    """Persist a new offer and optionally broadcast notifications."""

    company = _current_company()
    data = request.get_json() if request.is_json else request.form
    payload, error = _parse_offer_payload(data)
    if error:
        if request.is_json:
            return jsonify({"ok": False, "message": error}), HTTPStatus.BAD_REQUEST
        flash(error, "danger")
        return redirect(url_for("company_portal.list_offers"))

    offer = Offer(
        title=payload["title"],
        description=payload["description"],
        base_discount=payload["base_discount"],
        valid_until=payload["valid_until"],
        company_id=company.id,
    )
    db.session.add(offer)
    db.session.commit()

    if payload["send_notifications"]:
        broadcast_new_offer(offer.id)

    if request.is_json:
        return jsonify({"ok": True, "offer_id": offer.id})
    flash("Offer created successfully.", "success")
    return redirect(url_for("company_portal.list_offers"))


@company_portal.route(
    "/offers/<int:offer_id>/edit",
    endpoint="offer_edit",
)
@require_role("company")
def offer_edit(offer_id: int) -> str:
    """Return the pre-filled offer form for modal editing."""

    company = _current_company()
    offer = Offer.query.filter_by(company_id=company.id, id=offer_id).first_or_404()
    return render_template(
        "companies/offer_form.html",
        company=company,
        offer=offer,
        action_url=url_for("company_portal.offer_update", offer_id=offer_id),
        method="PUT",
    )


@company_portal.route(
    "/offers/<int:offer_id>",
    methods=["POST", "PUT"],
    endpoint="offer_update",
)
@require_role("company")
def offer_update(offer_id: int):
    """Update an existing offer ensuring it belongs to the current company."""

    company = _current_company()
    offer = Offer.query.filter_by(company_id=company.id, id=offer_id).first_or_404()

    data = request.get_json() if request.is_json else request.form
    payload, error = _parse_offer_payload(data)
    if error:
        if request.is_json:
            return jsonify({"ok": False, "message": error}), HTTPStatus.BAD_REQUEST
        flash(error, "danger")
        return redirect(url_for("company_portal.list_offers"))

    offer.title = payload["title"]
    offer.description = payload["description"]
    offer.base_discount = payload["base_discount"]
    offer.valid_until = payload["valid_until"]
    db.session.commit()

    if payload["send_notifications"]:
        broadcast_new_offer(offer.id)

    if request.is_json:
        return jsonify({"ok": True, "offer_id": offer.id})
    flash("Offer updated successfully.", "success")
    return redirect(url_for("company_portal.list_offers"))


@company_portal.route(
    "/offers/<int:offer_id>/delete",
    methods=["POST", "DELETE"],
    endpoint="offer_delete",
)
@require_role("company")
def offer_delete(offer_id: int):
    """Delete the specified offer owned by the current company."""

    company = _current_company()
    offer = Offer.query.filter_by(company_id=company.id, id=offer_id).first_or_404()
    db.session.delete(offer)
    db.session.commit()

    if request.is_json:
        return jsonify({"ok": True})
    flash("Offer removed successfully.", "success")
    return redirect(url_for("company_portal.list_offers"))
