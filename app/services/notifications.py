"""Notification service helpers and Celery tasks for asynchronous delivery."""

from __future__ import annotations

from typing import Any, Dict, Optional

from flask import current_app, url_for

from .. import app, celery, db
from ..models.notification import Notification
from ..models.offer import Offer
from ..models.user import User


def queue_notification(
    user_id: int,
    *,
    type: str,
    title: str,
    message: str,
    link_url: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """Queue a Celery task that persists a notification for the specified user."""

    payload = {
        "type": type,
        "title": title,
        "message": message,
        "link_url": link_url,
        "metadata": metadata or {},
    }
    return create_notification_task.delay(user_id=user_id, payload=payload)


def broadcast_new_offer(offer_id: int):
    """Queue a background job to broadcast a new offer notification."""

    return broadcast_offer_task.delay(offer_id=offer_id)


def notify_membership_upgrade(user_id: int, old_level: str, new_level: str):
    """Queue a membership upgrade notification for the provided user."""

    title = "Membership upgraded"
    message = f"Your membership tier has changed from {old_level} to {new_level}."
    metadata = {"old_level": old_level, "new_level": new_level}
    return queue_notification(
        user_id,
        type="membership_upgrade",
        title=title,
        message=message,
        link_url=url_for("portal.profile"),
        metadata=metadata,
    )


@celery.task(name="notifications.create")
def create_notification_task(user_id: int, payload: Dict[str, Any]):
    """Persist a notification record for the given user identifier."""

    with app.app_context():
        notification = Notification(
            user_id=user_id,
            type=payload.get("type"),
            title=payload.get("title"),
            message=payload.get("message"),
            link_url=payload.get("link_url"),
            metadata_json=(payload.get("metadata") or None),
        )
        db.session.add(notification)
        db.session.commit()
        current_app.logger.info(
            "Notification created for user %s with type %s", user_id, notification.type
        )
        return notification.id


@celery.task(name="notifications.broadcast_offer")
def broadcast_offer_task(offer_id: int, batch_size: int = 100):
    """Broadcast a new-offer notification to all users in configurable batches."""

    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    with app.app_context():
        offer = Offer.query.get(offer_id)
        if offer is None:
            current_app.logger.warning(
                "Skipping broadcast for missing offer_id=%s", offer_id
            )
            return 0

        total_created = 0
        query = User.query.order_by(User.id)
        offset = 0
        while True:
            users = query.offset(offset).limit(batch_size).all()
            if not users:
                break

            for user in users:
                notification = Notification(
                    user_id=user.id,
                    type="new_offer",
                    title=f"New offer: {offer.title}",
                    message=(
                        f"{offer.title} now includes at least {offer.base_discount:.2f}% off."
                    ),
                    link_url=url_for("portal.offers"),
                    metadata_json={
                        "offer_id": offer.id,
                        "membership_level": user.membership_level,
                        "base_discount": offer.base_discount,
                    },
                )
                db.session.add(notification)
                total_created += 1

            db.session.commit()
            offset += batch_size

        current_app.logger.info(
            "Broadcasted offer %s notifications to %s users", offer.id, total_created
        )
        return total_created


__all__ = [
    "queue_notification",
    "broadcast_new_offer",
    "notify_membership_upgrade",
    "create_notification_task",
    "broadcast_offer_task",
]
