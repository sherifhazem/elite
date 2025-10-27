"""Admin routes: notification APIs for listing and marking as read."""

from __future__ import annotations

from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request,
    jsonify,
    abort,
    Response,
)
from flask_login import current_user, login_required

from app import db
from app.models import User, Company, Offer, ActivityLog
from app.services.roles import admin_required

from ...services.notifications import (
    get_notifications_for_user,
    get_unread_count,
    mark_all_read,
)
from .. import admin


@admin.route("/api/notifications", methods=["GET"], endpoint="api_notifications_list")
@login_required
@admin_required
def api_notifications_list() -> Response:
    """Return a list of recent admin notifications with unread count."""

    limit = request.args.get("limit", default=20, type=int)

    if not current_user.is_authenticated:
        return jsonify({"unread": 0, "items": []}), 200

    unread = get_unread_count(current_user.id, sample_limit=limit)
    items = get_notifications_for_user(current_user.id, limit=limit)
    return jsonify({"unread": unread, "items": items}), 200


@admin.route("/api/notifications/read", methods=["POST"], endpoint="api_notifications_mark_read")
@admin_required
def api_notifications_mark_read() -> Response:
    """Mark all notifications as read for the current admin user."""

    mark_all_read(current_user.id)
    return jsonify({"status": "ok"})
