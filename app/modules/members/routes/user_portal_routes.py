# LINKED: Added logout flow for member portal (no design change)
# Implements proper session termination and user redirect while preserving full mobile-first UI.
# LINKED: Route alignment & aliasing for registration and dashboards (no schema changes)
# Updated templates to use endpoint-based url_for; README cleaned & synced with actual routes.
"""User portal blueprint exposing membership-aware pages."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional, Tuple

from urllib.parse import quote

from flask import Blueprint, Response, jsonify, redirect, render_template, request, url_for

from app.core.database import db
from app.modules.members.auth.utils import get_user_from_token
from app.models.notification import Notification
from app.models.offer import Offer
from app.models.user import User
from app.modules.members.services.notifications import (
    notify_membership_upgrade,
    notify_offer_feedback,
)
from app.modules.companies.services.offers import get_company_brief, get_portal_offers_with_company
from app.modules.members.services.redemption import list_user_redemptions_with_context

portal = Blueprint(
    "portal",
    __name__,
    url_prefix="/portal",
    template_folder="../templates/portal",
    static_folder="../static",
)


def _redirect_to_login() -> Response:
    """Redirect the current visitor to the login page with an optional return hint."""

    login_url = url_for("auth.login_page")
    next_target = request.full_path if request.query_string else request.path
    if next_target:
        normalized_next = next_target.rstrip("?")
        if normalized_next and not normalized_next.startswith(login_url):
            return redirect(f"{login_url}?next={quote(normalized_next, safe='/?=&')}")
    return redirect(login_url)


@portal.after_request
def _portal_no_cache(response: Response) -> Response:
    """Prevent caching of member portal views to avoid stale authenticated content."""

    response.headers.setdefault(
        "Cache-Control", "no-store, no-cache, must-revalidate, max-age=0"
    )
    response.headers.setdefault("Pragma", "no-cache")
    response.headers.setdefault("Expires", "0")
    return response


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


def _membership_card_payload(user: Optional[User], membership_level: str) -> Dict[str, str]:
    """Return metadata required to paint the digital membership card."""

    code = "000000"
    joined = "—"
    name = "ضيف ELITE"
    if user is not None:
        code = f"{user.id:06d}"
        if user.joined_at:
            joined = user.joined_at.strftime("%Y-%m-%d")
        name = user.username or name

    return {
        "code": code,
        "joined": joined,
        "name": name,
        "level": membership_level or "Basic",
        "level_key": (membership_level or "Basic").strip().lower() or "basic",
    }


# Render the portal home view summarizing the member's benefits.
@portal.route("/", methods=["GET"], endpoint="home")
def home():
    user, membership_level = _resolve_user_context()
    if user is None:
        return _redirect_to_login()
    featured_offers = Offer.query.order_by(Offer.created_at.desc()).limit(6).all()
    return render_template(
        "portal/home.html",
        user=user,
        membership_level=membership_level,
        featured_offers=featured_offers,
        notification_unread_count=_unread_notification_count(user),
        active_nav="home",
        current_year=datetime.utcnow().year,
    )


@portal.route("/home", methods=["GET"], endpoint="home_alias")
def home_alias():
    """Legacy alias to keep historic /portal/home links operational."""

    return redirect(url_for("portal.home"))


# Display the personalized offers list calculated for the user's tier.
@portal.route("/offers", methods=["GET"], endpoint="offers")
def offers():
    user, membership_level = _resolve_user_context()
    if user is None:
        return _redirect_to_login()
    offers_data = get_portal_offers_with_company(membership_level)
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
@portal.route("/profile", methods=["GET"], endpoint="profile")
def profile():
    user, membership_level = _resolve_user_context()
    if user is None:
        return _redirect_to_login()
    available_upgrades = []
    activations = []
    upgrade_success = request.args.get("upgraded") == "1"
    if user is not None:
        # Present only the membership tiers that are higher than the current one.
        current_rank = user.membership_rank()
        available_upgrades = [
            level
            for index, level in enumerate(User.MEMBERSHIP_LEVELS)
            if index > current_rank
        ]
    if user is not None:
        activations = list_user_redemptions_with_context(user.id)

    return render_template(
        "portal/profile.html",
        user=user,
        membership_level=membership_level,
        membership_card=_membership_card_payload(user, membership_level),
        available_upgrades=available_upgrades,
        upgrade_success=upgrade_success,
        activations=activations,
        notification_unread_count=_unread_notification_count(user),
        active_nav="profile",
        current_year=datetime.utcnow().year,
    )


@portal.route("/activations", methods=["GET"], endpoint="activations")
def user_activations():
    """Return the authenticated member's activations as JSON payload."""

    user, _ = _resolve_user_context()
    if user is None:
        return jsonify({"error": "Unauthorized"}), 401
    activations = list_user_redemptions_with_context(user.id)
    normalized = []
    for item in activations:
        normalized.append(
            {
                "id": item["id"],
                "status": item["status"],
                "redemption_code": item["redemption_code"],
                "created_at": item["created_at"].isoformat() if item["created_at"] else None,
                "redeemed_at": item["redeemed_at"].isoformat() if item["redeemed_at"] else None,
                "expires_at": item["expires_at"].isoformat() if item["expires_at"] else None,
                "offer": item["offer"],
                "company": item["company"],
            }
        )
    return jsonify({"items": normalized})


@portal.route(
    "/offers/<int:offer_id>/feedback",
    methods=["POST"],
    endpoint="offer_feedback",
)
def offer_feedback(offer_id: int):
    """Handle lightweight feedback interactions for the given offer."""

    user, _ = _resolve_user_context()
    if user is None:
        return jsonify({"error": "Unauthorized"}), 401
    offer = Offer.query.get_or_404(offer_id)
    if offer.company_id is None:
        return jsonify({"error": "Offer is not linked to a company."}), 400
    payload = request.get_json(silent=True) or {}
    action = (payload.get("action") or "like").strip().lower() or "like"
    note = (payload.get("note") or "").strip() or None
    notify_offer_feedback(
        company_id=offer.company_id,
        offer_id=offer.id,
        user_id=user.id,
        action=action,
        note=note,
    )
    return jsonify({"ok": True, "action": action})


@portal.route(
    "/companies/<int:company_id>", methods=["GET"], endpoint="company_brief"
)
def company_brief(company_id: int):
    """Return a lightweight company profile for the portal modal."""

    user, _ = _resolve_user_context()
    if user is None:
        return jsonify({"error": "Unauthorized"}), 401
    company = get_company_brief(company_id)
    if company is None:
        return jsonify({"error": "Company not found"}), 404
    return jsonify(company)


@portal.route("/notifications", methods=["GET"], endpoint="notifications")
def notifications():
    """Render the notifications center view for the authenticated member."""

    user, membership_level = _resolve_user_context()
    if user is None:
        return _redirect_to_login()
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


@portal.route("/upgrade", methods=["POST"], endpoint="upgrade_membership")
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
