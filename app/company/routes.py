# LINKED: Shared Offers & Redemptions Integration (no schema changes)
"""Blueprint implementing the company portal dashboard and management features."""
# UPDATED: Responsive Company Portal with Restricted Editable Fields.

from __future__ import annotations

# LINKED: Shared Offers & Redemptions Integration (no schema changes)
from datetime import datetime
from http import HTTPStatus
from typing import Dict, Optional, Tuple

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user as flask_current_user
from sqlalchemy import func

from .. import db
from ..models import Company, Offer, Redemption
from ..services.notifications import (
    broadcast_new_offer,
    fetch_offer_feedback_counts,
)
from ..services.offers import list_company_offers
from ..services.redemption import list_company_redemptions
from ..services.roles import require_role, resolve_user_from_request

company_portal_bp = Blueprint(
    "company_portal_bp",
    __name__,
    url_prefix="/company",
    template_folder="../templates/company",
)


@company_portal_bp.before_request
def _prevent_suspended_company_access():
    """Redirect suspended companies back to the login screen."""

    endpoint = request.endpoint or ""
    if not endpoint.startswith("company_portal_bp."):
        return None

    if endpoint == "company_portal_bp.complete_registration":
        return None

    user = getattr(g, "current_user", None)
    if user is None or not getattr(user, "is_authenticated", False):
        if getattr(flask_current_user, "is_authenticated", False):
            user = flask_current_user
    if user is None:
        user = resolve_user_from_request()

    if user is None or getattr(user, "role", "").strip().lower() != "company":
        return None

    company = getattr(user, "company", None)
    if company is None and getattr(user, "company_id", None):
        company = Company.query.get(user.company_id)

    if company and (company.status or "").strip().lower() == "suspended":
        flash("Your account is suspended. Please contact support.", "danger")
        return redirect(url_for("auth.login_page"))
    return None


def _ensure_company(user) -> Company:
    """Return the company linked to the provided user or abort with 403."""

    if user is None:
        abort(HTTPStatus.UNAUTHORIZED)

    company = getattr(user, "company", None)
    if company is None and getattr(user, "company_id", None):
        company = Company.query.get(user.company_id)

    if company is None:
        company = (
            Company.query.filter(Company.owner_user_id == user.id)
            .order_by(Company.id.asc())
            .first()
        )

    if company is None:
        abort(HTTPStatus.FORBIDDEN)

    if company.owner_user_id is None:
        company.owner_user_id = user.id
        db.session.commit()

    return company


def _current_company() -> Company:
    """Resolve the authenticated company using the global request context."""

    user = getattr(g, "current_user", None)
    return _ensure_company(user)


def _parse_offer_payload(data: Dict[str, str]) -> Tuple[Dict[str, object], str | None]:
    """Validate offer payload coming from forms or JSON requests."""

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


@company_portal_bp.route(
    "/complete_registration/<int:company_id>", methods=["GET", "POST"]
)
def complete_registration(company_id: int):
    """Allow a company to resubmit essential contact details for review."""

    company = Company.query.get_or_404(company_id)
    preferences = company.notification_settings()
    contact_number = getattr(company, "contact_number", None) or preferences.get(
        "contact_phone",
        "",
    )

    if request.method == "POST":
        company.name = (request.form.get("name") or company.name or "").strip()
        new_contact_number = (request.form.get("contact_number") or "").strip()
        if hasattr(company, "contact_number"):
            company.contact_number = new_contact_number
        else:
            updated_preferences = dict(preferences)
            updated_preferences["contact_phone"] = new_contact_number
            company.notification_preferences = updated_preferences
        company.set_status("pending")
        db.session.commit()
        flash("Your data has been resubmitted for review.", "info")
        return redirect(url_for("auth.login_page"))

    return render_template(
        "company/complete_registration.html",
        company=company,
        contact_number=contact_number,
    )


@company_portal_bp.route("/")
@require_role("company")
def index() -> str:
    """Redirect root portal requests to the dashboard view."""

    return redirect(url_for("company_portal_bp.dashboard"))


@company_portal_bp.route("/dashboard")
@require_role("company")
def dashboard() -> str:
    """Render the overview cards and latest redemption activity."""

    company = _current_company()

    active_offers = (
        Offer.query.filter(Offer.company_id == company.id)
        .filter(
            (Offer.valid_until.is_(None))
            | (Offer.valid_until >= datetime.utcnow())
        )
        .count()
    )
    total_redeemed = (
        Redemption.query.filter_by(company_id=company.id, status="redeemed")
        .with_entities(func.count(Redemption.id))
        .scalar()
    )
    unique_customers = (
        Redemption.query.filter_by(company_id=company.id)
        .with_entities(func.count(func.distinct(Redemption.user_id)))
        .scalar()
    )
    last_redemption = (
        Redemption.query.filter_by(company_id=company.id)
        .order_by(Redemption.redeemed_at.desc(), Redemption.created_at.desc())
        .first()
    )
    recent_redemptions = (
        Redemption.query.filter_by(company_id=company.id)
        .order_by(Redemption.created_at.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "company/dashboard.html",
        company=company,
        active_offers=active_offers,
        total_redeemed=total_redeemed,
        unique_customers=unique_customers,
        last_redemption=last_redemption,
        recent_redemptions=recent_redemptions,
    )


@company_portal_bp.route("/offers")
@require_role("company")
def offers() -> str:
    """Display the offer management table scoped to the current company."""

    company = _current_company()
    offers = (
        Offer.query.filter_by(company_id=company.id)
        .order_by(Offer.created_at.desc())
        .all()
    )
    feedback_totals = fetch_offer_feedback_counts(company.id)
    return render_template(
        "company/offers.html",
        company=company,
        offers=offers,
        now=datetime.utcnow(),
        feedback_totals=feedback_totals,
    )


@company_portal_bp.route("/offers/new")
@require_role("company")
def offer_new() -> str:
    """Render the offer creation form used inside the modal component."""

    company = _current_company()
    return render_template(
        "company/offer_form.html",
        company=company,
        offer=None,
        action_url=url_for("company_portal_bp.offer_create"),
        method="POST",
    )


@company_portal_bp.route("/offers", methods=["POST"])
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
        return redirect(url_for("company_portal_bp.offers"))

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
    return redirect(url_for("company_portal_bp.offers"))


@company_portal_bp.route("/offers/<int:offer_id>/edit")
@require_role("company")
def offer_edit(offer_id: int) -> str:
    """Return the pre-filled offer form for modal editing."""

    company = _current_company()
    offer = Offer.query.filter_by(company_id=company.id, id=offer_id).first_or_404()
    return render_template(
        "company/offer_form.html",
        company=company,
        offer=offer,
        action_url=url_for("company_portal_bp.offer_update", offer_id=offer_id),
        method="PUT",
    )


@company_portal_bp.route("/offers/<int:offer_id>", methods=["POST", "PUT"])
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
        return redirect(url_for("company_portal_bp.offers"))

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
    return redirect(url_for("company_portal_bp.offers"))


@company_portal_bp.route("/offers/<int:offer_id>/delete", methods=["POST", "DELETE"])
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
    return redirect(url_for("company_portal_bp.offers"))


@company_portal_bp.route("/redemptions")
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


@company_portal_bp.route("/redemptions/data")
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
                "created_at": redemption.created_at.isoformat() if redemption.created_at else None,
                "redeemed_at": redemption.redeemed_at.isoformat() if redemption.redeemed_at else None,
                "offer": {
                    "id": redemption.offer_id,
                    "title": redemption.offer.title if redemption.offer else f"Offer #{redemption.offer_id}",
                },
                "user": {
                    "id": redemption.user_id,
                    "username": redemption.user.username if redemption.user else None,
                    "email": redemption.user.email if redemption.user else None,
                },
            }
        )
    return jsonify({"items": items})


@company_portal_bp.route("/redemptions/verify", methods=["POST"])
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
        .filter(
            (Redemption.redemption_code == code)
            | (Redemption.qr_token == code)
        )
        .first()
    )
    if redemption is None:
        return jsonify({"ok": False, "message": "Code not found for this company."}), HTTPStatus.NOT_FOUND

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
            "created_at": redemption.created_at.isoformat() if redemption.created_at else None,
            "redeemed_at": redemption.redeemed_at.isoformat() if redemption.redeemed_at else None,
        }
    )


@company_portal_bp.route("/redemptions/confirm", methods=["POST"])
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

    current_app.logger.info(
        "Redemption %s confirmed by user %s", redemption.id, getattr(g, "current_user", None)
    )

    return jsonify({"ok": True, "status": redemption.status})


@company_portal_bp.route("/settings", methods=["GET", "POST"])
@require_role("company")
def settings():
    """Display and persist company profile metadata."""

    company = _current_company()

    if request.method == "POST":
        data = request.get_json() if request.is_json else request.form

        def _as_bool(raw_value) -> bool:
            if isinstance(raw_value, bool):
                return raw_value
            return str(raw_value).lower() in {"1", "true", "on", "yes"}

        proposed_name = (data.get("name") or "").strip()
        proposed_email = (data.get("account_email") or "").strip()
        proposed_registration = (data.get("registration_number") or "").strip()
        description = (data.get("description") or "").strip()
        logo_url = (data.get("logo_url") or "").strip()
        notifications_email = _as_bool(data.get("notify_email"))
        notifications_sms = _as_bool(data.get("notify_sms"))

        restricted_attempts = []
        if proposed_name and proposed_name != company.name:
            restricted_attempts.append("name")

        owner_email = ""
        if company.owner and getattr(company.owner, "email", None):
            owner_email = company.owner.email
        elif getattr(g, "current_user", None) and getattr(g.current_user, "email", None):
            owner_email = g.current_user.email
        if proposed_email and owner_email and proposed_email != owner_email:
            restricted_attempts.append("account_email")

        if hasattr(company, "registration_number"):
            current_registration = getattr(company, "registration_number") or ""
            if proposed_registration and proposed_registration != current_registration:
                restricted_attempts.append("registration_number")
            if not proposed_registration and current_registration:
                restricted_attempts.append("registration_number")

        if restricted_attempts:
            message = "هذا الحقل لا يمكن تعديله إلا بموافقة الإدارة."
            if request.is_json:
                return (
                    jsonify({
                        "ok": False,
                        "message": message,
                        "level": "warning",
                        "restricted": restricted_attempts,
                    }),
                    HTTPStatus.OK,
                )
            flash(message, "warning")
            return redirect(url_for("company_portal_bp.settings"))

        company.description = description or None
        company.logo_url = logo_url or None
        company.notification_preferences = {
            "email": notifications_email,
            "sms": notifications_sms,
        }
        db.session.commit()

        success_message = "تم حفظ التغييرات بنجاح."
        if request.is_json:
            return jsonify({"ok": True, "message": success_message})
        flash(success_message, "success")
        return redirect(url_for("company_portal_bp.settings"))

    return render_template(
        "company/settings.html",
        company=company,
        preferences=company.notification_settings(),
    )


__all__ = ["company_portal_bp"]
