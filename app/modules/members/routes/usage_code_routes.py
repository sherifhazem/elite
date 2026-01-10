"""API endpoints for member usage code verification."""

from __future__ import annotations

from http import HTTPStatus

from flask import Blueprint, g, jsonify, request

from app.core.database import db
from app.services.access_control import resolve_user_from_request
from app.services.usage_code_service import verify_usage_code

usage_codes = Blueprint("usage_codes", __name__, url_prefix="/api/usage-codes")


def _current_user():
    user = getattr(g, "current_user", None)
    if user is None:
        user = resolve_user_from_request()
        if user is not None:
            g.current_user = user
    return user


def _normalize_role(user) -> str:
    if user is None:
        return ""
    if hasattr(user, "normalized_role"):
        return (user.normalized_role or "member").lower()
    return str(getattr(user, "role", "member")).strip().lower()


@usage_codes.route("/verify", methods=["POST"])
def verify_usage_code_endpoint():
    """Verify a usage code submitted by a member for a specific offer."""

    user = _current_user()
    if user is None:
        return jsonify({"error": "Unauthorized"}), HTTPStatus.UNAUTHORIZED
    if not getattr(user, "is_active", False):
        return jsonify({"error": "Inactive account"}), HTTPStatus.FORBIDDEN
    if _normalize_role(user) not in {"member", "admin", "superadmin"}:
        return jsonify({"error": "Only members can verify usage codes."}), HTTPStatus.FORBIDDEN

    payload = {
        k: v
        for k, v in (getattr(request, "cleaned", {}) or {}).items()
        if not k.startswith("__")
    }
    offer_id = payload.get("offer_id")
    code = (payload.get("code") or "").strip()
    if offer_id in (None, "") or not code:
        return (
            jsonify({"error": "offer_id and code are required."}),
            HTTPStatus.BAD_REQUEST,
        )

    try:
        offer_identifier = int(offer_id)
    except (TypeError, ValueError):
        return jsonify({"error": "offer_id must be numeric."}), HTTPStatus.BAD_REQUEST

    result = verify_usage_code(member_id=user.id, offer_id=offer_identifier, code=code)
    db.session.commit()
    return jsonify(result), HTTPStatus.OK


__all__ = ["usage_codes"]
