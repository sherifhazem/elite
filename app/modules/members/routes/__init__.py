"""Blueprint definitions for the ELITE backend routes."""

from datetime import datetime
from http import HTTPStatus

from flask import Blueprint, jsonify, redirect, request, url_for

from .offer_routes import offers
from .redemption_routes import redemption
from .notification_routes import notifications
from .user_routes import users
from .user_portal_routes import portal
from app.modules.members.services.roles import resolve_user_from_request
from app import csrf
from core.observability.frontend_handler import record_api_trace, record_frontend_error, record_ui_event
from core.observability.utils import get_request_id


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
        return redirect(url_for("company_portal.dashboard"))
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


@csrf.exempt
@main.route("/log/frontend-error", methods=["POST"])
def log_frontend_error():
    """Capture frontend JavaScript errors and persist them to disk."""

    payload = request.get_json(silent=True) or {}
    payload.setdefault("timestamp", datetime.utcnow().isoformat() + "Z")
    payload.setdefault("page_url", request.headers.get("Referer", request.url))
    payload["request_id"] = get_request_id()
    record_frontend_error(payload)
    return (
        jsonify({"status": "logged", "request_id": payload["request_id"]}),
        HTTPStatus.CREATED,
    )


@csrf.exempt
@main.route("/log/api-trace", methods=["POST"])
def log_api_trace():
    """Capture API tracing information from the browser."""

    payload = request.get_json(silent=True) or {}
    payload.setdefault("timestamp", datetime.utcnow().isoformat() + "Z")
    payload["request_id"] = get_request_id()
    status_code = int(payload.get("status", 0) or 0)
    record_api_trace(payload, failure=status_code >= 400)
    return (
        jsonify({"status": "logged", "request_id": payload["request_id"]}),
        HTTPStatus.CREATED,
    )


@csrf.exempt
@main.route("/log/ui-event", methods=["POST"])
def log_ui_event():
    """Capture significant UI events for local observability."""

    payload = request.get_json(silent=True) or {}
    payload.setdefault("timestamp", datetime.utcnow().isoformat() + "Z")
    payload["request_id"] = get_request_id()
    record_ui_event(payload)
    return (
        jsonify({"status": "logged", "request_id": payload["request_id"]}),
        HTTPStatus.CREATED,
    )


__all__ = [
    "main",
    "users",
    "offers",
    "redemption",
    "portal",
    "notifications",
]
