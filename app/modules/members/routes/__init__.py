"""Blueprint definitions for the ELITE backend routes."""

from flask import Blueprint, jsonify, redirect, url_for

from .offer_routes import offers
from .redemption_routes import redemption
from .notification_routes import notifications
from .user_routes import users
from .user_portal_routes import portal
from .usage_code_routes import usage_codes
from app.services.access_control import resolve_user_from_request


main = Blueprint("main", __name__)


# Render the landing page for the Elite Discounts platform.
@main.route("/", methods=["GET"])
def index():
    """Redirect visitors to the appropriate experience based on their JWT role."""

    user = resolve_user_from_request()
    if user is None:
        return redirect(url_for("auth.login_page"))

    role = getattr(user, "role", "member").strip().lower()
    if role == "company":
        return redirect(url_for("company_portal.company_dashboard_overview"))
    if role in {"admin", "superadmin"}:
        return redirect(url_for("admin.dashboard_home"))
    return redirect(url_for("portal.member_portal_home"))


# Provide a simple about page describing the platform.
@main.route("/about", methods=["GET"])
def about():
    """Return a brief description of the platform."""

    return "About Elite Discounts"


# Expose the health check endpoint for uptime monitoring.
@main.route("/health", methods=["GET"])
def health_check():
    """Return a simple JSON response to confirm the service is healthy."""

    return jsonify({"status": "ok"})


__all__ = [
    "main",
    "users",
    "offers",
    "redemption",
    "portal",
    "notifications",
    "usage_codes",
]
