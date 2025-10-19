"""Blueprint definitions for the ELITE backend routes."""

from flask import Blueprint, jsonify, redirect, url_for

from .company_routes import company_routes
from .offer_routes import offer_routes
from .redemption_routes import redemption_bp
from .notification_routes import notif_bp
from .user_routes import user_routes
from .user_portal_routes import portal_bp
from ..services.roles import resolve_user_from_request


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
        return redirect(url_for("company_portal_bp.dashboard"))
    if role in {"admin", "superadmin"}:
        return redirect(url_for("admin.dashboard_home"))
    return redirect(url_for("portal.home"))


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
    "user_routes",
    "company_routes",
    "offer_routes",
    "redemption_bp",
    "portal_bp",
    "notif_bp",
]
