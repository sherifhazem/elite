"""Notification blueprint exposing REST endpoints for in-app messages."""

from __future__ import annotations

from typing import Dict, Optional

from flask import Blueprint, jsonify, request, g

from .. import db
from ..auth.utils import get_user_from_token
from ..models.notification import Notification

notif_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")


def _extract_token() -> Optional[str]:
    """Return a JWT token from the request headers or cookies."""

    authorization = request.headers.get("Authorization", "").strip()
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() == "bearer" and token:
        return token
    cookie_token = request.cookies.get("elite_token")
    if cookie_token:
        return cookie_token
    return None


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


@notif_bp.before_request
def _require_authentication():
    """Ensure the incoming request is tied to an authenticated user."""

    token = _extract_token()
    user = get_user_from_token(token) if token else None
    if user is None:
        return jsonify({"error": "Authentication required."}), 401
    g.current_user = user
    return None


@notif_bp.route("/", methods=["GET"])
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


@notif_bp.route("/<int:notification_id>/read", methods=["PUT"])
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


@notif_bp.route("/read-all", methods=["PUT"])
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


@notif_bp.route("/<int:notification_id>", methods=["DELETE"])
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


__all__ = ["notif_bp"]
