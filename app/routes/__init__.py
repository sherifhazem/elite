"""Blueprint definitions for the ELITE backend routes."""

from flask import Blueprint, jsonify, render_template

from .company_routes import company_routes
from .offer_routes import offer_routes
from .user_routes import user_routes
from .user_portal_routes import portal_bp


main = Blueprint("main", __name__)


# Render the landing page for the Elite Discounts platform.
@main.route("/", methods=["GET"])
def index():
    """Return the homepage template."""

    return render_template("index.html")


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
    "portal_bp",
]
