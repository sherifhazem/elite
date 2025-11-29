"""Redemption workflows for the company portal."""

from __future__ import annotations

from datetime import datetime
from http import HTTPStatus
from typing import Optional

from flask import current_app, g, jsonify, render_template, request

from app import db
from app.models import Redemption
from app.modules.companies.services.offers import list_company_offers
from app.modules.members.services.redemption import list_company_redemptions
from app.services.access_control import require_role
from core.observability.logger import log_event
from . import company_portal
from app.utils.company_context import _ensure_company, _current_company


@company_portal.route("/redemptions", endpoint="redemptions")
@require_role("company")
def redemptions() -> str:
    """Render the redemption history with contextual filters."""

    company = _current_company()
    offer_id = request.args.get("offer_id", type=int)
    status = request.args.get("status", type=str)
    if status not in {None, "pending", "redeemed", "expired"}:
        status = None

    start_date_raw = request.args.get("start_date", type=str)
    end_date_raw = request.args.get("end_date", type=str)

    def _normalize_date(value: Optional[str], *, end: bool = False) -> Optional[datetime]:
        if not value:
            return None
        try:
            parsed = datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return None
        if end:
            return parsed.replace(hour=23, minute=59, second=59, microsecond=999999)
        return parsed

    start_date = _normalize_date(start_date_raw)
    end_date = _normalize_date(end_date_raw, end=True)

    filters = {
        "offer_id": offer_id,
        "status": status,
        "start_date": start_date_raw or "",
        "end_date": end_date_raw or "",
    }

    recent_redemptions = list_company_redemptions(
        company.id,
        offer_id=offer_id,
        status=status,
        date_range=(start_date, end_date),
        limit=200,
    )
    available_offers = list_company_offers(company.id)
    return render_template(
        "company/redemptions.html",
        company=company,
        filters=filters,
        available_offers=available_offers,
        recent_redemptions=recent_redemptions,
    )


@company_portal.route("/redemptions/data", endpoint="redemptions_data")
@require_role("company")
def redemptions_data():
    """Return company redemption history as JSON for live refreshing."""

    company = _current_company()
    offer_id = request.args.get("offer_id", type=int)
    status = request.args.get("status", type=str)
    if status not in {None, "pending", "redeemed", "expired"}:
        status = None

    start_date_raw = request.args.get("start_date", type=str)
    end_date_raw = request.args.get("end_date", type=str)

    def _normalize(value: Optional[str], *, end: bool = False) -> Optional[datetime]:
        if not value:
            return None
        try:
            parsed = datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return None
        if end:
            return parsed.replace(hour=23, minute=59, second=59, microsecond=999999)
        return parsed

    start_date = _normalize(start_date_raw)
    end_date = _normalize(end_date_raw, end=True)

    redemptions = list_company_redemptions(
        company.id,
        offer_id=offer_id,
        status=status,
        date_range=(start_date, end_date),
        limit=300,
    )
    items = []
    for redemption in redemptions:
        items.append(
            {
                "id": redemption.id,
                "code": redemption.redemption_code,
                "status": redemption.status,
                "created_at": redemption.created_at.isoformat()
                if redemption.created_at
                else None,
                "redeemed_at": redemption.redeemed_at.isoformat()
                if redemption.redeemed_at
                else None,
                "offer": {
                    "id": redemption.offer_id,
                    "title": redemption.offer.title
                    if redemption.offer
                    else f"Offer #{redemption.offer_id}",
                },
                "user": {
                    "id": redemption.user_id,
                    "username": redemption.user.username if redemption.user else None,
                    "email": redemption.user.email if redemption.user else None,
                },
            }
        )
    return jsonify({"items": items})


@company_portal.route(
    "/redemptions/verify",
    methods=["POST"],
    endpoint="verify_redemption",
)
@require_role("company")
def verify_redemption():
    """Validate a redemption code or QR token for the current company."""

    company = _current_company()
    data = request.get_json() if request.is_json else request.form
    code = (data.get("code") or data.get("qr_token") or "").strip()
    if not code:
        return jsonify({"ok": False, "message": "Code is required."}), HTTPStatus.BAD_REQUEST

    redemption = (
        Redemption.query.filter_by(company_id=company.id)
        .filter((Redemption.redemption_code == code) | (Redemption.qr_token == code))
        .first()
    )
    if redemption is None:
        return (
            jsonify({"ok": False, "message": "Code not found for this company."}),
            HTTPStatus.NOT_FOUND,
        )

    if redemption.is_expired():
        redemption.mark_expired()
        db.session.commit()
        return jsonify({"ok": False, "message": "Code is expired."}), HTTPStatus.GONE

    return jsonify(
        {
            "ok": True,
            "redemption_id": redemption.id,
            "status": redemption.status,
            "user": redemption.user.username if redemption.user else None,
            "created_at": redemption.created_at.isoformat()
            if redemption.created_at
            else None,
            "redeemed_at": redemption.redeemed_at.isoformat()
            if redemption.redeemed_at
            else None,
        }
    )


@company_portal.route(
    "/redemptions/confirm",
    methods=["POST"],
    endpoint="confirm_redemption",
)
@require_role("company")
def confirm_redemption():
    """Mark a verified redemption as redeemed after staff confirmation."""

    company = _current_company()
    data = request.get_json() if request.is_json else request.form
    redemption_id = data.get("redemption_id")
    code = (data.get("code") or "").strip()

    query = Redemption.query.filter_by(company_id=company.id)
    if redemption_id:
        redemption = query.filter_by(id=int(redemption_id)).first()
    else:
        redemption = query.filter(
            (Redemption.redemption_code == code) | (Redemption.qr_token == code)
        ).first()

    if redemption is None:
        return jsonify({"ok": False, "message": "Redemption not found."}), HTTPStatus.NOT_FOUND

    if redemption.status == "redeemed":
        return jsonify({"ok": False, "message": "Code already redeemed."}), HTTPStatus.CONFLICT

    if redemption.is_expired():
        redemption.mark_expired()
        db.session.commit()
        return jsonify({"ok": False, "message": "Code expired."}), HTTPStatus.GONE

    redemption.mark_redeemed()
    db.session.commit()

    log_event(
        level="INFO",
        event="route_checkpoint",
        source="route",
        module=__name__,
        function="validate_qr",  # function name from route definition
        message="Redemption confirmed",
        details={
            "redemption_id": redemption.id,
            "user_id": getattr(getattr(g, "current_user", None), "id", None),
        },
    )

    return jsonify({"ok": True, "status": redemption.status})
