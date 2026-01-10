"""Offer management routes for the company portal."""

from __future__ import annotations

import os
from datetime import datetime
from http import HTTPStatus
from typing import Dict, Set, Tuple

from flask import current_app, flash, jsonify, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

from app.core.database import db
from app.models import Offer
from app.models.offer import OFFER_CLASSIFICATION_TYPES, OfferClassification
from app.modules.members.services.member_notifications_service import (
    broadcast_new_offer,
    fetch_offer_feedback_counts,
)
from app.modules.admin.services import admin_settings_service
from app.services.access_control import company_required
from . import company_portal
from app.utils.company_context import _current_company


ALLOWED_OFFER_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "svg"}
CLASSIFICATION_LABELS = {
    "first_time_offer": "First-time offer",
    "loyalty_offer": "Loyalty offer",
    "active_members_only": "Active members only",
    "happy_hour": "Happy hour",
    "mid_week": "Mid-week",
}


def _get_offer_type_availability() -> Dict[str, bool]:
    """Return admin-controlled availability for each classification key."""

    admin_settings = admin_settings_service.get_admin_settings()
    offer_types = admin_settings.get("offer_types", {})
    availability: Dict[str, bool] = {}
    for key in OFFER_CLASSIFICATION_TYPES:
        availability[key] = bool(offer_types.get(key, False))
    return availability


def _as_bool(raw_value) -> bool:
    if isinstance(raw_value, bool):
        return raw_value
    return str(raw_value).lower() in {"true", "1", "on", "yes"}


def _get_request_payload() -> Dict[str, object]:
    """Return the submitted data regardless of the request format."""

    if request.is_json:
        return request.get_json(silent=True) or {}

    cleaned = getattr(request, "cleaned", {}) or {}
    if cleaned:
        return {k: v for k, v in cleaned.items() if not k.startswith("__")}

    if request.form:
        form_data = request.form.to_dict()
        # Preserve multi-select values such as classifications
        form_data["classifications"] = request.form.getlist("classifications")
        return form_data

    return {}


def _parse_offer_payload(
    data: Dict[str, str],
    existing_offer: Offer | None = None,
    *,
    allowed_classifications: Set[str] | None = None,
) -> Tuple[Dict[str, object], str | None]:
    """Normalize incoming fields while preserving existing values when omitted."""

    def _coalesce(key: str, default: str = "") -> str:
        if key in data and data[key] not in {None, ""}:
            return str(data[key])
        if existing_offer is not None and hasattr(existing_offer, key):
            value = getattr(existing_offer, key)
            if value is None:
                return ""
            if isinstance(value, datetime):
                return value.strftime("%Y-%m-%d")
            return str(value)
        return default

    title = _coalesce("title").strip()
    description = (data.get("description") or getattr(existing_offer, "description", "") or "").strip()
    base_discount_raw = _coalesce(
        "base_discount",
        str(getattr(existing_offer, "base_discount", "0")),
    ).strip()
    start_date_raw = (data.get("start_date") or data.get("valid_from") or "").strip()
    valid_until_raw = (data.get("valid_until") or data.get("end_date") or "").strip()
    status = _coalesce("status", getattr(existing_offer, "status", "active"))
    send_notifications = _as_bool(data.get("send_notifications", False))
    image_url = (data.get("image_url") or getattr(existing_offer, "image_url", "") or "").strip()

    if status not in {"active", "paused", "archived"}:
        return {}, "Status must be one of: active, paused, archived."

    if not title:
        return {}, "Title is required."

    try:
        base_discount = float(base_discount_raw)
    except ValueError:
        return {}, "Base discount must be numeric."

    start_date = None
    if start_date_raw:
        try:
            start_date = datetime.strptime(start_date_raw, "%Y-%m-%d")
        except ValueError:
            return {}, "Start date must follow YYYY-MM-DD format."
    elif existing_offer is not None:
        start_date = existing_offer.start_date

    valid_until = None
    if valid_until_raw:
        try:
            valid_until = datetime.strptime(valid_until_raw, "%Y-%m-%d")
        except ValueError:
            return {}, "Valid until must follow YYYY-MM-DD format."
    elif existing_offer is not None:
        valid_until = existing_offer.valid_until

    if start_date and valid_until and start_date > valid_until:
        return {}, "Start date cannot be later than the end date."

    has_classifications = "classifications" in data
    raw_classifications = data.get("classifications", [])
    if not has_classifications and existing_offer is not None:
        raw_classifications = existing_offer.classification_values
    if isinstance(raw_classifications, str):
        raw_classifications = [raw_classifications]
    classifications = [value.strip() for value in raw_classifications if str(value).strip()]
    invalid_classifications = [c for c in classifications if c not in OFFER_CLASSIFICATION_TYPES]
    if invalid_classifications:
        return {}, "One or more classifications are not supported."

    if allowed_classifications is not None:
        disabled_selected = [
            classification
            for classification in classifications
            if classification not in allowed_classifications
        ]
        if disabled_selected:
            readable = [CLASSIFICATION_LABELS.get(value, value) for value in disabled_selected]
            return {}, (
                "The following classifications are disabled by Admin Settings: "
                + ", ".join(readable)
                + "."
            )

    payload = {
        "title": title,
        "description": description or None,
        "base_discount": base_discount,
        "start_date": start_date,
        "valid_until": valid_until,
        "image_url": image_url or None,
        "status": status,
        "send_notifications": send_notifications,
        "classifications": list(dict.fromkeys(classifications)),
    }
    return payload, None


def _apply_classifications(offer: Offer, classifications: list[str]) -> None:
    """Synchronize offer classifications with the provided collection."""

    desired = set(classifications)
    existing = {record.classification: record for record in offer.classifications}

    for value in desired - set(existing):
        offer.classifications.append(OfferClassification(classification=value))

    for value in set(existing) - desired:
        db.session.delete(existing[value])


def _handle_offer_image_upload(offer: Offer) -> str:
    """Persist an uploaded offer image and return the public URL."""

    upload = request.files.get("image_file")
    if upload is None or upload.filename == "":
        return offer.image_url or ""

    filename = secure_filename(upload.filename)
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in ALLOWED_OFFER_IMAGE_EXTENSIONS:
        raise ValueError("Unsupported file type. Please upload PNG, JPG, or WEBP.")

    max_bytes = 4 * 1024 * 1024
    if upload.content_length and upload.content_length > max_bytes:
        raise ValueError("File exceeds the 4MB size limit.")

    target_dir = os.path.join(
        current_app.root_path,
        "modules",
        "companies",
        "static",
        "companies",
        "uploads",
        "offers",
        str(offer.company_id),
    )
    os.makedirs(target_dir, exist_ok=True)

    timestamp = int(datetime.utcnow().timestamp())
    stored_name = f"offer-{offer.id or 'new'}-{timestamp}.{extension}"
    target_path = os.path.join(target_dir, stored_name)
    upload.save(target_path)

    return f"/static/companies/uploads/offers/{offer.company_id}/{stored_name}?v={timestamp}"


@company_portal.route("/offers", methods=["GET"], endpoint="company_offers_list")
@company_required
def company_offers_list() -> str:
    """Display the offer management table scoped to the current company."""

    company = _current_company()
    offers = (
        Offer.query.filter_by(company_id=company.id)
        .order_by(Offer.created_at.desc())
        .all()
    )
    feedback_totals = fetch_offer_feedback_counts(company.id)
    return render_template(
        "companies/offers_list.html",
        company=company,
        offers=offers,
        now=datetime.utcnow(),
        feedback_totals=feedback_totals,
    )


@company_portal.route("/offers/new", endpoint="offer_new")
@company_required
def offer_new() -> str:
    """Render the offer creation form in a dedicated workspace."""

    company = _current_company()
    offer_type_availability = _get_offer_type_availability()
    return render_template(
        "companies/offer_editor.html",
        company=company,
        offer=None,
        action_url=url_for("company_portal.offer_create"),
        page_title="Create Offer",
        classification_choices=CLASSIFICATION_LABELS,
        classification_availability=offer_type_availability,
    )


@company_portal.route("/offers", methods=["POST"], endpoint="offer_create")
@company_required
def offer_create():
    """Persist a new offer and optionally broadcast notifications."""

    company = _current_company()
    offer_type_availability = _get_offer_type_availability()
    allowed_classifications = {
        key for key, enabled in offer_type_availability.items() if enabled
    }
    data = _get_request_payload()
    payload, error = _parse_offer_payload(
        data, allowed_classifications=allowed_classifications
    )
    if error:
        if request.is_json:
            return jsonify({"ok": False, "message": error}), HTTPStatus.BAD_REQUEST
        flash(error, "danger")
        return redirect(url_for("company_portal.company_offers_list"))

    offer = Offer(
        title=payload["title"],
        description=payload["description"],
        base_discount=payload["base_discount"],
        start_date=payload["start_date"],
        status=payload["status"],
        valid_until=payload["valid_until"],
        image_url=payload["image_url"],
        company_id=company.id,
    )
    db.session.add(offer)
    db.session.flush()

    _apply_classifications(offer, payload["classifications"])

    try:
        image_url = _handle_offer_image_upload(offer)
    except ValueError as exc:
        error_message = str(exc)
        db.session.rollback()
        if request.is_json:
            return jsonify({"ok": False, "message": error_message}), HTTPStatus.BAD_REQUEST
        flash(error_message, "danger")
        return redirect(url_for("company_portal.company_offers_list"))

    if image_url and image_url != offer.image_url:
        offer.image_url = image_url

    db.session.commit()

    if payload["send_notifications"]:
        broadcast_new_offer(offer.id)

    if request.is_json:
        return jsonify({"ok": True, "offer_id": offer.id})
    flash("Offer created successfully.", "success")
    return redirect(url_for("company_portal.company_offers_list"))


@company_portal.route(
    "/offers/<int:offer_id>/edit",
    endpoint="offer_edit",
)
@company_required
def offer_edit(offer_id: int) -> str:
    """Return the pre-filled offer form for inline editing."""

    company = _current_company()
    offer = Offer.query.filter_by(company_id=company.id, id=offer_id).first_or_404()
    offer_type_availability = _get_offer_type_availability()
    return render_template(
        "companies/offer_editor.html",
        company=company,
        offer=offer,
        action_url=url_for("company_portal.offer_update", offer_id=offer_id),
        page_title="Edit Offer",
        classification_choices=CLASSIFICATION_LABELS,
        classification_availability=offer_type_availability,
    )


@company_portal.route(
    "/offers/<int:offer_id>",
    methods=["POST", "PUT"],
    endpoint="offer_update",
)
@company_required
def offer_update(offer_id: int):
    """Update an existing offer ensuring it belongs to the current company."""

    company = _current_company()
    offer = Offer.query.filter_by(company_id=company.id, id=offer_id).first_or_404()

    offer_type_availability = _get_offer_type_availability()
    allowed_classifications = {
        key for key, enabled in offer_type_availability.items() if enabled
    }
    data = _get_request_payload()
    payload, error = _parse_offer_payload(
        data,
        existing_offer=offer,
        allowed_classifications=allowed_classifications,
    )
    if error:
        if request.is_json:
            return jsonify({"ok": False, "message": error}), HTTPStatus.BAD_REQUEST
        flash(error, "danger")
        return redirect(url_for("company_portal.company_offers_list"))

    offer.title = payload["title"]
    offer.description = payload["description"]
    offer.base_discount = payload["base_discount"]
    offer.start_date = payload["start_date"]
    offer.status = payload["status"]
    offer.valid_until = payload["valid_until"]
    offer.image_url = payload["image_url"]

    _apply_classifications(offer, payload["classifications"])

    try:
        image_url = _handle_offer_image_upload(offer)
    except ValueError as exc:
        error_message = str(exc)
        db.session.rollback()
        if request.is_json:
            return jsonify({"ok": False, "message": error_message}), HTTPStatus.BAD_REQUEST
        flash(error_message, "danger")
        return redirect(url_for("company_portal.company_offers_list"))

    if image_url and image_url != offer.image_url:
        offer.image_url = image_url

    db.session.commit()

    if payload["send_notifications"]:
        broadcast_new_offer(offer.id)

    if request.is_json:
        return jsonify({"ok": True, "offer_id": offer.id})
    flash("Offer updated successfully.", "success")
    return redirect(url_for("company_portal.company_offers_list"))


@company_portal.route(
    "/offers/<int:offer_id>/delete",
    methods=["POST", "DELETE"],
    endpoint="offer_delete",
)
@company_required
def offer_delete(offer_id: int):
    """Delete the specified offer owned by the current company."""

    company = _current_company()
    offer = Offer.query.filter_by(company_id=company.id, id=offer_id).first_or_404()
    db.session.delete(offer)
    db.session.commit()

    if request.is_json:
        return jsonify({"ok": True})
    flash("Offer removed successfully.", "success")
    return redirect(url_for("company_portal.company_offers_list"))
