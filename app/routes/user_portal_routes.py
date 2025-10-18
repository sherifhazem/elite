"""User portal blueprint exposing membership-aware pages."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple

from flask import Blueprint, jsonify, render_template, request, url_for

from .. import db
from ..auth.utils import get_user_from_token
from ..models.notification import Notification
from ..models.offer import Offer
from ..models.user import User
from ..services.notifications import notify_membership_upgrade

portal_bp = Blueprint("portal", __name__, url_prefix="/portal")


def _extract_token() -> Optional[str]:
    """Return a JWT token from headers or cookies when available."""

    authorization = request.headers.get("Authorization", "").strip()
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() == "bearer" and token:
        return token
    cookie_token = request.cookies.get("elite_token")
    if cookie_token:
        return cookie_token
    return None


def _resolve_user_context() -> Tuple[Optional[User], str]:
    """Return the authenticated user (if any) and normalized membership level."""

    membership_level = "Basic"
    user: Optional[User] = None

    token = _extract_token()
    if token:
        user = get_user_from_token(token)
        if user is not None and user.membership_level:
            membership_level = user.membership_level

    return user, membership_level or "Basic"


def _unread_notification_count(user: Optional[User]) -> int:
    """Return the unread notification count for the given user."""

    if user is None:
        return 0
    return Notification.query.filter_by(user_id=user.id, is_read=False).count()


# Render the portal home view summarizing the member's benefits.
@portal_bp.route("/", methods=["GET"])
def home():
    user, membership_level = _resolve_user_context()
    return render_template(
        "portal/home.html",
        user=user,
        membership_level=membership_level,
        notification_unread_count=_unread_notification_count(user),
        active_nav="home",
        current_year=datetime.utcnow().year,
    )


# Display the personalized offers list calculated for the user's tier.
@portal_bp.route("/offers", methods=["GET"])
def offers():
    user, membership_level = _resolve_user_context()
    offers_data = Offer.query.order_by(Offer.valid_until).all()
    return render_template(
        "portal/offers.html",
        user=user,
        membership_level=membership_level,
        offers=offers_data,
        notification_unread_count=_unread_notification_count(user),
        active_nav="offers",
        current_year=datetime.utcnow().year,
    )


# Present the member's profile details and upgrade prompts.
@portal_bp.route("/profile", methods=["GET"])
def profile():
    user, membership_level = _resolve_user_context()
    available_upgrades = []
    upgrade_success = request.args.get("upgraded") == "1"
    if user is not None:
        # Present only the membership tiers that are higher than the current one.
        current_rank = user.membership_rank()
        available_upgrades = [
            level
            for index, level in enumerate(User.MEMBERSHIP_LEVELS)
            if index > current_rank
        ]
    return render_template(
        "portal/profile.html",
        user=user,
        membership_level=membership_level,
        available_upgrades=available_upgrades,
        upgrade_success=upgrade_success,
        notification_unread_count=_unread_notification_count(user),
        active_nav="profile",
        current_year=datetime.utcnow().year,
    )


@portal_bp.route("/notifications", methods=["GET"])
def notifications():
    """Render the notifications center view for the authenticated member."""

    user, membership_level = _resolve_user_context()
    unread_count = _unread_notification_count(user)
    notifications_list = []
    if user is not None:
        notifications_list = (
            Notification.query.filter_by(user_id=user.id)
            .order_by(Notification.created_at.desc())
            .limit(200)
            .all()
        )
    return render_template(
        "portal/notifications.html",
        user=user,
        membership_level=membership_level,
        notifications=notifications_list,
        unread_count=unread_count,
        notification_unread_count=unread_count,
        active_nav="notifications",
        current_year=datetime.utcnow().year,
    )


@portal_bp.route("/upgrade", methods=["POST"])
def upgrade_membership():
    """Upgrade the authenticated user's membership level when permitted."""

    # Authenticate the request using the same helper leveraged by the portal views.
    token = _extract_token()
    user = get_user_from_token(token) if token else None
    if user is None:
        return jsonify({"error": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    desired_level = payload.get("new_level", "")
    normalized_level = User.normalize_membership_level(desired_level)
    if not normalized_level:
        return (
            jsonify({"error": "Invalid level", "allowed_levels": User.MEMBERSHIP_LEVELS}),
            400,
        )

    if not user.can_upgrade_to(normalized_level):
        return (
            jsonify({
                "error": "Upgrade not permitted",
                "message": "Choose a level higher than your current membership.",
            }),
            400,
        )

    try:
        previous_level = user.membership_level
        user.update_membership_level(normalized_level)
        db.session.commit()
    except ValueError as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 400

    notify_membership_upgrade(user.id, previous_level or "Basic", normalized_level)

    return (
        jsonify(
            {
                "message": f"Membership upgraded to {normalized_level}",
                "redirect_url": url_for("portal.profile", upgraded="1"),
                "new_level": normalized_level,
            }
        ),
        200,
    )
