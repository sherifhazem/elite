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
from app.models import Notification, Offer, User
from app.modules.members.auth.utils import AUTH_COOKIE_NAME, get_user_from_token
from app.modules.members.services.member_notifications_service import (
    notify_offer_feedback,
)
from app.modules.companies.services.company_offers_service import (
    get_company_brief,
    get_portal_offers_with_company,
)

from app.services.incentive_eligibility_service import get_offer_runtime_flags

portal = Blueprint(
    "portal",
    __name__,
    url_prefix="/portal",
    template_folder="../templates/members/portal",
    static_folder="../static/members",
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
    cookie_token = request.cookies.get(AUTH_COOKIE_NAME)
    if cookie_token:
        return cookie_token
    return None


def _resolve_user_context() -> Optional[User]:
    """Return the authenticated user (if any)."""

    user: Optional[User] = None

    token = _extract_token()
    if token:
        user = get_user_from_token(token)

    return user


def _unread_notification_count(user: Optional[User]) -> int:
    """Return the unread notification count for the given user."""

    if user is None:
        return 0
    return Notification.query.filter_by(user_id=user.id, is_read=False).count()


def _membership_card_payload(user: Optional[User]) -> Dict[str, str]:
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
    }


# Render the portal home view summarizing the member's benefits.
@portal.route("/", methods=["GET"], endpoint="member_portal_home")
def member_portal_home():
    user = _resolve_user_context()
    if user is None:
        return _redirect_to_login()
    featured_offers = get_portal_offers_with_company(limit=6, featured=True)
    return render_template(
        "members/portal/home.html",
        user=user,
        featured_offers=featured_offers,
        notification_unread_count=_unread_notification_count(user),
        active_nav="home",
        current_year=datetime.utcnow().year,
    )


@portal.route("/home", methods=["GET"], endpoint="member_portal_home_alias")
def member_portal_home_alias():
    """Legacy alias to keep historic /portal/home links operational."""

    return redirect(url_for("portal.member_portal_home"))


# Display the personalized offers list calculated for the user's tier.
@portal.route("/offers", methods=["GET"], endpoint="member_portal_offers")
def member_portal_offers():
    user = _resolve_user_context()
    if user is None:
        return _redirect_to_login()
    offers_data = get_portal_offers_with_company()
    offer_runtime_flags = {
        offer.id: get_offer_runtime_flags(user.id if user else None, offer.id)
        for offer in offers_data
    }
    return render_template(
        "members/portal/offers.html",
        user=user,
        offers=offers_data,
        offer_runtime_flags=offer_runtime_flags,
        notification_unread_count=_unread_notification_count(user),
        active_nav="offers",
        current_year=datetime.utcnow().year,
    )


# Present the member's profile details and upgrade prompts.
@portal.route("/profile", methods=["GET"], endpoint="member_portal_profile")
def member_portal_profile():
    user = _resolve_user_context()
    if user is None:
        return _redirect_to_login()


    return render_template(
        "members/portal/profile.html",
        user=user,
        membership_card=_membership_card_payload(user),
        notification_unread_count=_unread_notification_count(user),
        active_nav="profile",
        current_year=datetime.utcnow().year,
    )





@portal.route(
    "/offers/<int:offer_id>/feedback",
    methods=["POST"],
    endpoint="offer_feedback",
)
def offer_feedback(offer_id: int):
    """Handle lightweight feedback interactions for the given offer."""

    user = _resolve_user_context()
    if user is None:
        return jsonify({"error": "Unauthorized"}), 401
    offer = Offer.query.get_or_404(offer_id)
    if offer.company_id is None:
        return jsonify({"error": "Offer is not linked to a company."}), 400
    payload = {k: v for k, v in (getattr(request, "cleaned", {}) or {}).items() if not k.startswith("__")}
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

    user = _resolve_user_context()
    if user is None:
        return jsonify({"error": "Unauthorized"}), 401
    company = get_company_brief(company_id)
    if company is None:
        return jsonify({"error": "Company not found"}), 404
    return jsonify(company)


@portal.route("/notifications", methods=["GET"], endpoint="member_portal_notifications")
def member_portal_notifications():
    """Render the notifications center view for the authenticated member."""

    user = _resolve_user_context()
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
        "members/portal/notifications.html",
        user=user,
        notifications=notifications_list,
        unread_count=unread_count,
        notification_unread_count=unread_count,
        active_nav="notifications",
        current_year=datetime.utcnow().year,
    )
