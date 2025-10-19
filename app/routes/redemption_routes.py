# LINKED: Shared Offers & Redemptions Integration (no schema changes)
"""Blueprint exposing the offer redemption API endpoints."""

from __future__ import annotations

import os
# LINKED: Shared Offers & Redemptions Integration (no schema changes)
from http import HTTPStatus

from flask import (
    Blueprint,
    current_app,
    g,
    jsonify,
    request,
    send_from_directory,
    url_for,
)

from .. import db
from ..models import Redemption, User
from ..services.notifications import (
    notify_offer_redemption_activity,
    queue_notification,
)
from ..services.redemption import (
    create_redemption,
    generate_qr_token,
    get_redemption_status,
    mark_redeemed,
)
from ..services.roles import resolve_user_from_request

redemption_bp = Blueprint("redemptions", __name__, url_prefix="/api/redemptions")


def _current_user():
    """Return the authenticated user for the request if available."""

    user = getattr(g, "current_user", None)
    if user is None:
        user = resolve_user_from_request()
        if user is not None:
            g.current_user = user
    return user


def _normalize_role(user) -> str:
    """Return the normalized role string for the provided user object."""

    if user is None:
        return ""
    if hasattr(user, "normalized_role"):
        return (user.normalized_role or "member").lower()
    return str(getattr(user, "role", "member")).strip().lower()


def _serialize_response(redemption: Redemption, data: dict) -> dict:
    """Augment redemption payloads with presentation-friendly fields."""

    payload = dict(data or {})
    if redemption is not None:
        offer_title = redemption.offer.title if redemption.offer else f"Offer #{redemption.offer_id}"
        payload.setdefault("offer_title", offer_title)
        payload.setdefault("company_id", redemption.company_id)
        payload.setdefault("offer_id", redemption.offer_id)
        payload.setdefault("user_id", redemption.user_id)
        company = redemption.offer.company if redemption.offer and redemption.offer.company else redemption.company
        if company is not None:
            payload.setdefault("company_name", company.name)
            payload.setdefault("company_summary", (company.description or "")[:160])
        payload.setdefault("offer_description", redemption.offer.description if redemption.offer else "")
        payload.setdefault(
            "created_at", redemption.created_at.isoformat() if redemption.created_at else None
        )
        payload.setdefault(
            "expires_at", redemption.expires_at.isoformat() if redemption.expires_at else None
        )
    payload["qr_url"] = url_for(
        "redemptions.get_qrcode_image", code=payload.get("code") or redemption.redemption_code, _external=True
    )
    return payload


@redemption_bp.route("/", methods=["POST"])
def create_redemption_endpoint():
    """Create a new redemption code for the authenticated member."""

    user = _current_user()
    if user is None:
        return jsonify({"error": "Unauthorized"}), HTTPStatus.UNAUTHORIZED
    if not getattr(user, "is_active", False):
        return jsonify({"error": "Inactive account"}), HTTPStatus.FORBIDDEN
    if _normalize_role(user) not in {"member", "admin", "superadmin"}:
        return jsonify({"error": "Only members can activate offers."}), HTTPStatus.FORBIDDEN

    payload = request.get_json(silent=True) or {}
    offer_id = payload.get("offer_id")
    if offer_id in (None, ""):
        return jsonify({"error": "offer_id is required."}), HTTPStatus.BAD_REQUEST

    try:
        offer_identifier = int(offer_id)
    except (TypeError, ValueError):
        return jsonify({"error": "offer_id must be numeric."}), HTTPStatus.BAD_REQUEST

    try:
        redemption = create_redemption(user.id, offer_identifier)
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), HTTPStatus.BAD_REQUEST
    except Exception as exc:  # pragma: no cover - defensive logging
        db.session.rollback()
        current_app.logger.exception("Failed to create redemption", exc_info=True)
        return jsonify({"error": "Unable to create redemption at this time."}), HTTPStatus.INTERNAL_SERVER_ERROR

    status_payload = get_redemption_status(redemption.redemption_code) or {}
    response = _serialize_response(redemption, status_payload)
    notify_offer_redemption_activity(
        redemption=redemption,
        event="activated",
        timestamp=redemption.created_at,
    )
    return jsonify(response), HTTPStatus.CREATED


@redemption_bp.route("/<string:code>", methods=["GET"])
def redemption_status(code: str):
    """Return the redemption status for the requested code."""

    normalized_code = (code or "").strip().upper()
    data = get_redemption_status(normalized_code)
    if data is None:
        return jsonify({"error": "Redemption not found."}), HTTPStatus.NOT_FOUND

    user = _current_user()
    if user is None:
        return jsonify({"error": "Unauthorized"}), HTTPStatus.UNAUTHORIZED
    if not getattr(user, "is_active", False):
        return jsonify({"error": "Account disabled"}), HTTPStatus.FORBIDDEN

    role = _normalize_role(user)
    company = getattr(user, "company", None)
    if role in {"admin", "superadmin"}:
        allowed = True
    elif role == "company":
        allowed = company is not None and data.get("company_id") == getattr(company, "id", None)
    else:
        allowed = data.get("user_id") == getattr(user, "id", None)

    if not allowed:
        return jsonify({"error": "Forbidden"}), HTTPStatus.FORBIDDEN

    redemption = Redemption.query.filter_by(redemption_code=normalized_code).first()
    response = _serialize_response(redemption, data) if redemption else data
    return jsonify(response), HTTPStatus.OK


@redemption_bp.route("/<string:code>/confirm", methods=["PUT"])
def confirm_redemption(code: str):
    """Confirm redemption usage for the company linked to the authenticated user."""

    user = _current_user()
    if user is None:
        return jsonify({"error": "Unauthorized"}), HTTPStatus.UNAUTHORIZED
    if not getattr(user, "is_active", False):
        return jsonify({"error": "Inactive account"}), HTTPStatus.FORBIDDEN
    if _normalize_role(user) not in {"company", "superadmin"}:
        return jsonify({"error": "Only company accounts can confirm redemptions."}), HTTPStatus.FORBIDDEN

    company = getattr(user, "company", None)
    if company is None:
        return jsonify({"error": "Your account is not linked to a company."}), HTTPStatus.BAD_REQUEST

    redemption = Redemption.query.filter_by(redemption_code=(code or "").strip().upper()).first()
    if redemption is None:
        return jsonify({"error": "Redemption not found."}), HTTPStatus.NOT_FOUND
    previous_status = redemption.status
    previous_redeemed_at = redemption.redeemed_at

    payload = request.get_json(silent=True) or {}
    qr_token = payload.get("qr_token") or payload.get("token")

    try:
        updated = mark_redeemed(redemption.redemption_code, company_id=company.id, qr_token=qr_token)
    except LookupError:
        return jsonify({"error": "Redemption not found."}), HTTPStatus.NOT_FOUND
    except PermissionError:
        return jsonify({"error": "This redemption is not associated with your company."}), HTTPStatus.FORBIDDEN
    except ValueError as exc:
        return jsonify({"error": str(exc)}), HTTPStatus.BAD_REQUEST
    except Exception as exc:  # pragma: no cover - defensive logging
        current_app.logger.exception("Failed to confirm redemption", exc_info=True)
        return jsonify({"error": "Unable to confirm redemption."}), HTTPStatus.INTERNAL_SERVER_ERROR

    status_payload = get_redemption_status(updated.redemption_code) or {}
    response = _serialize_response(updated, status_payload)
    response.setdefault("message", "Offer Redeemed Successfully")

    status_changed = (
        previous_status != updated.status
        or (updated.redeemed_at and previous_redeemed_at != updated.redeemed_at)
    )
    if status_changed and updated.status == "redeemed":
        try:
            queue_notification(
                updated.user_id,
                type="offer_redeemed",
                title="تم استخدام العرض بنجاح",
                message=f"تم اعتماد الكود {updated.redemption_code} من قبل {company.name}.",
                link_url=url_for("portal.profile"),
                metadata={
                    "offer_id": updated.offer_id,
                    "company_id": updated.company_id,
                    "redemption_code": updated.redemption_code,
                },
            )
        except Exception:  # pragma: no cover - notification failures should not break API
            current_app.logger.exception("Failed to queue redemption notification for member", exc_info=True)

        admin_users = (
            User.query.filter(User.role.in_(["admin", "superadmin"]), User.is_active.is_(True)).all()
        )
        for admin in admin_users:
            try:
                queue_notification(
                    admin.id,
                    type="offer_redeemed_admin",
                    title="Offer redemption confirmed",
                    message=(
                        f"Company {company.name} confirmed redemption {updated.redemption_code}."
                    ),
                    link_url=url_for("reports.reports_home"),
                    metadata={
                        "offer_id": updated.offer_id,
                        "company_id": updated.company_id,
                        "redemption_code": updated.redemption_code,
                    },
                )
            except Exception:  # pragma: no cover - notification failures should not break API
                current_app.logger.exception("Failed to queue admin redemption notification", exc_info=True)

    return jsonify(response), HTTPStatus.OK


@redemption_bp.route("/<string:code>/qrcode", methods=["GET"])
def get_qrcode_image(code: str):
    """Return the QR code image associated with the redemption code."""

    redemption = Redemption.query.filter_by(redemption_code=(code or "").strip().upper()).first()
    if redemption is None:
        return jsonify({"error": "Redemption not found."}), HTTPStatus.NOT_FOUND

    if redemption.status == "pending" and redemption.is_expired():
        redemption.mark_expired()
        db.session.commit()
        return jsonify({"error": "Redemption expired."}), HTTPStatus.GONE

    directory = os.path.join(current_app.static_folder or "static", "qrcodes")
    filename = f"{redemption.redemption_code}.png"
    file_path = os.path.join(directory, filename)

    if not os.path.exists(file_path):
        try:
            generate_qr_token(redemption.redemption_code, commit=False, regenerate=False)
        except Exception as exc:  # pragma: no cover - defensive logging
            current_app.logger.exception("Failed to generate QR token", exc_info=True)
            return jsonify({"error": "Unable to generate QR code."}), HTTPStatus.INTERNAL_SERVER_ERROR

    if not os.path.exists(file_path):
        return jsonify({"error": "QR code not available."}), HTTPStatus.NOT_FOUND

    return send_from_directory(directory, filename, mimetype="image/png")


__all__ = ["redemption_bp"]
