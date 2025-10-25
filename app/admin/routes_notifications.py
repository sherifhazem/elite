# -*- coding: utf-8 -*-
"""Admin notification API endpoints backed by Redis."""

from flask import jsonify, request
from flask_login import current_user, login_required

from app.admin import admin
from app.services.notifications import (
    get_notifications_for_user,
    get_unread_count,
    mark_all_read,
)
from app.services.roles import admin_required


@admin.route("/api/notifications", methods=["GET"])
@login_required
@admin_required
def api_notifications_list():
    """Return a list of recent admin notifications with unread count."""

    limit = request.args.get("limit", default=20, type=int)

    if not current_user.is_authenticated:
        return jsonify({"unread": 0, "items": []}), 200

    unread = get_unread_count(current_user.id, sample_limit=limit)
    items = get_notifications_for_user(current_user.id, limit=limit)
    return jsonify({"unread": unread, "items": items}), 200


@admin.route("/api/notifications/read", methods=["POST"])
@admin_required
def api_notifications_mark_read():
    """Mark all notifications as read for the current admin user."""

    mark_all_read(current_user.id)
    return jsonify({"status": "ok"})
