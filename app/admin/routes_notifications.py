# -*- coding: utf-8 -*-
"""Admin notification API endpoints backed by Redis."""

from flask import jsonify, request
from flask_login import current_user

from app.admin import admin
from app.services.notifications import (
    list_admin_notifications,
    get_unread_count,
    mark_all_read,
)
from app.services.roles import admin_required


@admin.route("/api/notifications", methods=["GET"])
@admin_required
def api_notifications_list():
    """Return recent notifications alongside the unread count."""

    limit = int(request.args.get("limit", 20))
    data = list_admin_notifications(limit=limit)
    unread = get_unread_count(current_user.id, sample_limit=limit)
    return jsonify({"items": data, "unread": unread})


@admin.route("/api/notifications/read", methods=["POST"])
@admin_required
def api_notifications_mark_read():
    """Mark all notifications as read for the current admin user."""

    mark_all_read(current_user.id)
    return jsonify({"status": "ok"})
