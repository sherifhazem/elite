"""Notification blueprint exposing REST endpoints for in-app messages."""

from __future__ import annotations

from typing import Dict

from flask import Blueprint, jsonify, request, g

from app.core.database import db
from app.modules.members.auth.utils import get_user_from_token
from app.models.notification import Notification
from app.services.access_control import _extract_token

notifications = Blueprint("notifications", __name__, url_prefix="/api/notifications")


def _serialize_notification(notification: Notification) -> Dict[str, object]:
    """Return a dictionary representation suitable for JSON responses."""

    return {
        "id": notification.id,
        "type": notification.type,
        "title": notification.title,
        "message": notification.message,
        "link_url": notification.link_url,
        "is_read": notification.is_read,
        "created_at": notification.created_at.isoformat()
        if notification.created_at
        else None,
        "metadata": notification.metadata_json or {},
    }


@notifications.before_request
def _require_authentication():
    """Ensure the incoming request is tied to an authenticated user."""

    token = _extract_token()
    user = get_user_from_token(token) if token else None
    if user is None:
        return jsonify({"error": "Authentication required."}), 401
    g.current_user = user
    return None


@notifications.route("/", methods=["GET"], endpoint="list_notifications")
def list_notifications():
    """Return a paginated list of notifications for the current user."""

    user = g.current_user
    try:
        page = max(int(request.args.get("page", 1)), 1)
    except (TypeError, ValueError):
        page = 1
    try:
        per_page = max(min(int(request.args.get("per_page", 20)), 100), 1)
    except (TypeError, ValueError):
        per_page = 20

    pagination = (
        Notification.query.filter_by(user_id=user.id)
        .order_by(Notification.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    unread_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()

    return (
        jsonify(
            {
                "notifications": [
                    _serialize_notification(notification)
                    for notification in pagination.items
                ],
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "unread_count": unread_count,
            }
        ),
        200,
    )


@notifications.route(
    "/<int:notification_id>/read", methods=["PUT"], endpoint="mark_notification_read"
)
def mark_notification_read(notification_id: int):
    """Mark a specific notification as read for the current user."""

    user = g.current_user
    notification = Notification.query.filter_by(
        id=notification_id, user_id=user.id
    ).first()
    if notification is None:
        return jsonify({"error": "Notification not found."}), 404

    notification.is_read = True
    db.session.commit()

    return jsonify({"status": "updated", "notification": _serialize_notification(notification)}), 200


@notifications.route("/read-all", methods=["PUT"], endpoint="mark_all_notifications_read")
def mark_all_notifications_read():
    """Mark all notifications for the current user as read."""

    user = g.current_user
    updated = (
        Notification.query.filter_by(user_id=user.id, is_read=False)
        .update({"is_read": True}, synchronize_session=False)
    )
    if updated:
        db.session.commit()

    return jsonify({"status": "updated", "updated_count": int(updated)}), 200


@notifications.route("/<int:notification_id>", methods=["DELETE"], endpoint="delete_notification")
def delete_notification(notification_id: int):
    """Delete a notification belonging to the current user."""

    user = g.current_user
    notification = Notification.query.filter_by(
        id=notification_id, user_id=user.id
    ).first()
    if notification is None:
        return jsonify({"error": "Notification not found."}), 404

    db.session.delete(notification)
    db.session.commit()
    return jsonify({"status": "deleted"}), 200


__all__ = ["notifications"]
