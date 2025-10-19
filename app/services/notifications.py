# LINKED: Shared Offers & Redemptions Integration (no schema changes)
# ADDED: Auto welcome notifications for new members, companies, and staff (no DB schema change).
"""Notification service helpers and Celery tasks for asynchronous delivery."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence

from flask import current_app, url_for
from sqlalchemy.orm import joinedload

from .. import app, celery, db
from ..models.notification import Notification
from ..models.offer import Offer
from ..models.user import User


WELCOME_NOTIFICATION_TEMPLATES: Dict[str, Dict[str, Optional[str]]] = {
    "member": {
        "title": "🎉 أهلاً بك في برنامج ELITE!",
        "message": (
            "مرحبًا {username},\n"
            "يسعدنا انضمامك إلى مجتمع ELITE المميز.\n"
            "يمكنك الآن الاستفادة من العروض الحصرية والخصومات المتاحة عبر حسابك.\n\n"
            "نرحب بك مجددًا،\n"
            "فريق ELITE."
        ),
        "link_endpoint": "portal.offers",
    },
    "company": {
        "title": "🤝 مرحبًا بشركائنا الجدد في ELITE!",
        "message": (
            "مرحبًا {company_name},\n"
            "شكرًا لانضمامكم إلى منصة ELITE.\n"
            "يمكنكم الآن إضافة عروضكم الخاصة وجذب المزيد من العملاء من خلال بوابتكم المخصصة.\n\n"
            "نتمنى لكم نجاحًا مستمرًا،\n"
            "فريق ELITE."
        ),
        "link_endpoint": "company_portal_bp.dashboard",
    },
    "staff": {
        "title": "👋 مرحبًا بك في فريق ELITE الإداري!",
        "message": (
            "مرحبًا {username},\n"
            "تم إنشاء حسابك بنجاح ضمن فريق ELITE.\n"
            "يمكنك الآن تسجيل الدخول وبدء العمل على إدارة المهام الموكلة إليك.\n\n"
            "بالتوفيق،\n"
            "إدارة ELITE."
        ),
        "link_endpoint": "admin.dashboard_home",
    },
}


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


def ensure_welcome_notification(user: User, *, context: Optional[str] = None) -> Optional[int]:
    """Create a one-time welcome notification tailored to the user's role.

    The helper checks for an existing notification tagged with the same welcome
    context before queueing a new one to avoid duplicate greetings.
    """

    if user is None or not getattr(user, "id", None):
        return None

    normalized_role = (context or user.normalized_role).strip().lower()
    if normalized_role == "staff":
        template_key = "staff"
    elif normalized_role in {"admin", "superadmin"}:
        template_key = "staff"
    elif normalized_role == "company":
        template_key = "company"
    else:
        template_key = "member"

    username = (getattr(user, "username", "") or "").strip() or user.email
    company_name = ""
    if template_key == "company":
        company_name = getattr(getattr(user, "company", None), "name", "") or ""
        if not company_name:
            try:
                owned_company = user.owned_companies.first()
            except Exception:  # pragma: no cover - dynamic loader guard
                owned_company = None
            if owned_company:
                company_name = owned_company.name
    if not company_name:
        company_name = username

    render_context = {"username": username, "company_name": company_name}
    template = WELCOME_NOTIFICATION_TEMPLATES.get(template_key)
    if not template:
        return None

    title = template["title"].format(**render_context)
    message = template["message"].format(**render_context)

    existing_notifications: Sequence[Notification] = (
        Notification.query.filter_by(user_id=user.id, type="welcome_message").all()
    )
    for notification in existing_notifications:
        metadata = notification.metadata_json or {}
        if metadata.get("welcome_context") == template_key:
            return notification.id
        if notification.title == title and notification.message == message:
            return notification.id

    link_url: Optional[str] = None
    endpoint = template.get("link_endpoint")
    if endpoint:
        try:
            link_url = url_for(endpoint)
        except RuntimeError:
            link_url = None

    metadata = {"welcome_context": template_key}
    return queue_notification(
        user.id,
        type="welcome_message",
        title=title,
        message=message,
        link_url=link_url,
        metadata=metadata,
    )


def _company_recipient_ids(company_id: int) -> List[int]:
    """Return company-associated user identifiers for notification delivery."""

    if not company_id:
        return []
    recipients: List[int] = []
    company_users: Iterable[User] = (
        User.query.filter_by(company_id=company_id, is_active=True).all()
    )
    recipients.extend(user.id for user in company_users if user.id not in recipients)

    owner_ids = (
        db.session.query(User.id)
        .filter(User.is_active.is_(True), User.owned_companies.any(id=company_id))
        .all()
    )
    for (user_id,) in owner_ids:
        if user_id not in recipients:
            recipients.append(user_id)
    return recipients


def notify_offer_redemption_activity(
    *,
    redemption,
    event: str = "activated",
    timestamp: Optional[datetime] = None,
) -> None:
    """Send offer redemption notifications to both the member and company."""

    if redemption is None:
        return

    resolved_timestamp = timestamp or redemption.redeemed_at or redemption.created_at
    metadata = {
        "offer_id": redemption.offer_id,
        "company_id": redemption.company_id,
        "user_id": redemption.user_id,
        "redemption_code": redemption.redemption_code,
        "event": event,
        "redeemed_at": resolved_timestamp.isoformat() if resolved_timestamp else None,
    }

    try:
        queue_notification(
            redemption.user_id,
            type="offer_redeemed",
            title="تم تفعيل العرض",
            message=f"تم إنشاء رمز {redemption.redemption_code} لعرضك.",
            link_url=url_for("portal.profile"),
            metadata=metadata,
        )
    except Exception:  # pragma: no cover - defensive notification guard
        current_app.logger.exception(
            "Failed to queue redemption notification for member", exc_info=True
        )

    for recipient_id in _company_recipient_ids(redemption.company_id):
        try:
            queue_notification(
                recipient_id,
                type="offer_redeemed",
                title="تم إنشاء تفعيل جديد",
                message=(
                    f"العضو #{redemption.user_id} أنشأ كود {redemption.redemption_code} للعرض"
                ),
                link_url=url_for("company_portal_bp.redemptions"),
                metadata=metadata,
            )
        except Exception:  # pragma: no cover - defensive notification guard
            current_app.logger.exception(
                "Failed to queue redemption notification for company", exc_info=True
            )


def notify_offer_feedback(
    *,
    company_id: int,
    offer_id: int,
    user_id: int,
    action: str,
    note: Optional[str] = None,
) -> None:
    """Send a lightweight feedback notification to company recipients."""

    metadata = {
        "offer_id": offer_id,
        "user_id": user_id,
        "company_id": company_id,
        "action": action,
    }
    if note:
        metadata["note"] = note

    for recipient_id in _company_recipient_ids(company_id):
        try:
            queue_notification(
                recipient_id,
                type="offer_feedback",
                title="تفاعل جديد مع العرض",
                message="أحد الأعضاء تفاعل مع أحد عروضك.",
                link_url=url_for("company_portal_bp.offers"),
                metadata=metadata,
            )
        except Exception:  # pragma: no cover - defensive notification guard
            current_app.logger.exception(
                "Failed to queue offer feedback notification", exc_info=True
            )


def fetch_offer_feedback_counts(company_id: int) -> Dict[int, int]:
    """Return aggregated feedback counts per offer for the company."""

    if not company_id:
        return {}

    notifications: Sequence[Notification] = (
        Notification.query.options(joinedload(Notification.user))
        .join(User, User.id == Notification.user_id)
        .filter(
            Notification.type == "offer_feedback",
            User.is_active.is_(True),
            (User.company_id == company_id)
            | (User.owned_companies.any(id=company_id)),
        )
        .order_by(Notification.created_at.desc())
        .all()
    )

    counts: Dict[int, int] = {}
    for notification in notifications:
        metadata = notification.metadata_json or {}
        offer_id = metadata.get("offer_id")
        if not offer_id:
            continue
        counts[offer_id] = counts.get(offer_id, 0) + 1
    return counts


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
    "ensure_welcome_notification",
    "notify_membership_upgrade",
    "notify_offer_redemption_activity",
    "notify_offer_feedback",
    "fetch_offer_feedback_counts",
    "create_notification_task",
    "broadcast_offer_task",
]
