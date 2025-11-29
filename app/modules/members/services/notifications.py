# LINKED: Registration Flow & Welcome Notification Review (Users & Companies)
# Verified welcome email and internal notification triggers for new accounts.
# ADDED: Admin Communication Center – bulk/group message system (no DB schema change).
# LINKED: Shared Offers & Redemptions Integration (no schema changes)
# ADDED: Auto welcome notifications for new members, companies, and staff (no DB schema change).
"""Notification service helpers and Celery tasks for asynchronous delivery."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set

from flask import current_app, url_for
from sqlalchemy.orm import joinedload

from app import app, celery, db, redis_client
from app.models import Notification
from app.models.offer import Offer
from app.models.user import User
from core.observability.logger import log_event


# Redis-backed admin notification keys and defaults
ADMIN_NOTIF_LIST_KEY = "admin:notifications"
ADMIN_NOTIF_LAST_SEEN_KEY = "admin:last_seen:{user_id}"

MAX_LIST_SIZE = 500
DEFAULT_TTL_DAYS = 14


def _log(function: str, event: str, message: str, details: Dict[str, object] | None = None, level: str = "INFO") -> None:
    """Emit standardized observability events for notification services."""

    log_event(
        level=level,
        event=event,
        source="service",
        module=__name__,
        function=function,
        message=message,
        details=details,
    )


WELCOME_NOTIFICATION_TEMPLATES: Dict[str, Dict[str, Optional[str]]] = {
    "member": {
        "title": "مرحبًا بك في ELITE",
        "message": (
            "مرحبًا بكم في عائلة ELITE!\n"
            "استمتع بالعروض المميزة والخصومات المخصصة لمستواك منذ لحظة تسجيلك."
        ),
        "type": "welcome_user",
        "link_endpoint": "portal.offers",
    },
    "company": {
        "title": "مرحبًا بكم في ELITE للشركات",
        "message": (
            "مرحبًا بكم في منصة ELITE للشركات!\n"
            "يمكنكم الآن إدارة عروضكم ومتابعة تفاعلات الأعضاء بسهولة من لوحة التحكم الخاصة بكم."
        ),
        "type": "welcome_company",
        "link_endpoint": "company_portal.dashboard",
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
        "type": "welcome_staff",
        "link_endpoint": "admin.dashboard_home",
    },
}


def send_welcome_notification(
    user_or_company,
    *,
    context: Optional[str] = None,
) -> Optional[int]:
    """Persist a welcome notification for a new member or company account."""

    if user_or_company is None:
        _log(
            "send_welcome_notification",
            "validation_failure",
            "No user or company provided for welcome notification",
            level="ERROR",
        )
        return None

    _log(
        "send_welcome_notification",
        "service_start",
        "Preparing welcome notification",
        {"context": context, "user_id": getattr(user_or_company, "id", None)},
    )

    template_key = (context or "").strip().lower()
    target_user: Optional[User] = None
    company_name = ""

    if isinstance(user_or_company, User):
        target_user = user_or_company
        normalized_role = target_user.normalized_role
        if template_key:
            normalized_role = template_key
        if normalized_role in {"admin", "superadmin", "staff"}:
            template_key = "staff"
        elif normalized_role == "company":
            template_key = "company"
            company_name = getattr(getattr(target_user, "company", None), "name", "")
            if not company_name:
                try:
                    owned = target_user.owned_companies.first()
                except Exception:  # pragma: no cover - dynamic loader guard
                    owned = None
                if owned:
                    company_name = owned.name
        else:
            template_key = "member"
    else:
        CompanyModel = None
        try:
            from ..models.company import Company as CompanyModel  # type: ignore
        except Exception:  # pragma: no cover - import guard
            CompanyModel = None  # type: ignore

        if CompanyModel and isinstance(user_or_company, CompanyModel):
            company = user_or_company
            template_key = "company"
            company_name = getattr(company, "name", "")
            target_user = getattr(company, "owner", None)
            if target_user is None and getattr(company, "owner_user_id", None):
                target_user = User.query.get(company.owner_user_id)
        else:
            return None

    template = WELCOME_NOTIFICATION_TEMPLATES.get(template_key or "member")
    if not template or target_user is None:
        _log(
            "send_welcome_notification",
            "soft_failure",
            "No welcome template resolved",
            {"context": template_key},
            level="WARNING",
        )
        return None

    recipient_name = (
        company_name.strip()
        if template_key == "company" and company_name
        else (getattr(target_user, "username", "") or target_user.email).strip()
    )
    render_context = {
        "username": getattr(target_user, "username", ""),
        "company_name": company_name or recipient_name,
        "recipient_name": recipient_name,
    }

    title = template["title"].format(**render_context)
    message = template["message"].format(**render_context)
    notification_type = template.get("type") or (
        "welcome_company" if template_key == "company" else "welcome_user"
    )

    existing = (
        Notification.query.filter_by(user_id=target_user.id, type=notification_type)
        .order_by(Notification.id.desc())
        .first()
    )
    if existing:
        metadata = existing.metadata_json or {}
        if metadata.get("message") == message:
            _log(
                "send_welcome_notification",
                "service_checkpoint",
                "Existing welcome notification reused",
                {"notification_id": existing.id},
            )
            return existing.id

    link_url: Optional[str] = None
    endpoint = template.get("link_endpoint")
    if endpoint:
        try:
            link_url = url_for(endpoint)
        except RuntimeError:
            link_url = None

    metadata = {
        "recipient_name": recipient_name,
        "timestamp": datetime.utcnow().isoformat(),
        "message": message,
    }

    notification = Notification(
        user_id=target_user.id,
        type=notification_type,
        title=title,
        message=message,
        link_url=link_url,
        metadata_json=metadata,
    )
    db.session.add(notification)
    db.session.commit()
    _log(
        "send_welcome_notification",
        "db_write_success",
        "Welcome notification created",
        {"notification_id": notification.id, "user_id": target_user.id},
    )
    return notification.id


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

    _log(
        "queue_notification",
        "service_start",
        "Queueing notification for user",
        {"user_id": user_id, "type": type},
    )
    payload = {
        "type": type,
        "title": title,
        "message": message,
        "link_url": link_url,
        "metadata": metadata or {},
    }
    result = create_notification_task.delay(user_id=user_id, payload=payload)
    _log(
        "queue_notification",
        "service_complete",
        "Notification enqueued",
        {"user_id": user_id, "task_id": getattr(result, "id", None)},
    )
    return result


def broadcast_new_offer(offer_id: int):
    """Queue a background job to broadcast a new offer notification."""

    _log(
        "broadcast_new_offer",
        "service_start",
        "Scheduling broadcast for new offer",
        {"offer_id": offer_id},
    )
    result = broadcast_offer_task.delay(offer_id=offer_id)
    _log(
        "broadcast_new_offer",
        "service_complete",
        "Broadcast task queued",
        {"offer_id": offer_id, "task_id": getattr(result, "id", None)},
    )
    return result


def send_admin_broadcast_notifications(
    user_ids: Sequence[int],
    *,
    subject: str,
    message: str,
    sent_by: Optional[int] = None,
) -> int:
    """Send admin broadcast notifications to the provided user identifiers."""

    unique_ids: Set[int] = {int(user_id) for user_id in user_ids if user_id}
    if not unique_ids:
        _log(
            "send_admin_broadcast_notifications",
            "validation_failure",
            "No admin recipients provided",
            level="WARNING",
        )
        return 0

    _log(
        "send_admin_broadcast_notifications",
        "service_start",
        "Queueing admin broadcast notifications",
        {"recipients": len(unique_ids)},
    )
    metadata = {
        "subject": subject,
        "message": message,
        "sent_by": sent_by,
        "sent_at": datetime.utcnow().isoformat() + "Z",
    }

    created = 0
    for user_id in sorted(unique_ids):
        queue_notification(
            user_id,
            type="admin_broadcast",
            title=subject,
            message=message,
            metadata=metadata,
        )
        created += 1

    _log(
        "send_admin_broadcast_notifications",
        "service_complete",
        "Admin broadcast notifications queued",
        {"recipients": created},
    )
    return created


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
    """Compatibility wrapper that delegates to :func:`send_welcome_notification`."""

    if user is None or not getattr(user, "id", None):
        return None

    return send_welcome_notification(user, context=context)


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
        _log(
            "notify_offer_redemption_activity",
            "request_error",
            "Failed to queue redemption notification for member",
            {"redemption_code": redemption.redemption_code},
            level="ERROR",
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
                link_url=url_for("company_portal.redemptions"),
                metadata=metadata,
            )
        except Exception:  # pragma: no cover - defensive notification guard
            _log(
                "notify_offer_redemption_activity",
                "request_error",
                "Failed to queue redemption notification for company",
                {"redemption_code": redemption.redemption_code, "recipient_id": recipient_id},
                level="ERROR",
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
                link_url=url_for("company_portal.list_offers"),
                metadata=metadata,
            )
        except Exception:  # pragma: no cover - defensive notification guard
            _log(
                "notify_offer_feedback",
                "request_error",
                "Failed to queue offer feedback notification",
                {"company_id": company_id, "offer_id": offer_id, "recipient_id": recipient_id},
                level="ERROR",
            )


def fetch_offer_feedback_counts(company_id: int) -> Dict[int, int]:
    """Return aggregated feedback counts per offer for the company."""

    if not company_id:
        return {}

    _log(
        "fetch_offer_feedback_counts",
        "service_start",
        "Aggregating feedback counts",
        {"company_id": company_id},
    )
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
    _log(
        "fetch_offer_feedback_counts",
        "service_complete",
        "Feedback counts prepared",
        {"company_id": company_id, "offer_count": len(counts)},
    )
    return counts


@celery.task(name="notifications.create")
def create_notification_task(user_id: int, payload: Dict[str, Any]):
    """Persist a notification record for the given user identifier."""

    with app.app_context():
        _log(
            "create_notification_task",
            "service_start",
            "Creating notification from Celery task",
            {"user_id": user_id, "type": payload.get("type")},
        )
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
        _log(
            "create_notification_task",
            "db_write_success",
            "Notification created via Celery",
            {"user_id": user_id, "notification_id": notification.id},
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
            _log(
                "broadcast_offer_task",
                "soft_failure",
                "Skipping broadcast for missing offer",
                {"offer_id": offer_id},
                level="WARNING",
            )
            return 0

        _log(
            "broadcast_offer_task",
            "service_start",
            "Broadcasting offer notifications",
            {"offer_id": offer.id, "batch_size": batch_size},
        )
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

        _log(
            "broadcast_offer_task",
            "service_complete",
            "Broadcasted offer notifications",
            {"offer_id": offer.id, "total_created": total_created},
        )
        return total_created


def _now_iso() -> str:
    """Return the current UTC timestamp formatted as ISO-8601 with a Z suffix."""

    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def push_admin_notification(
    event_type: str,
    title: str,
    message: str,
    link: str = "",
    *,
    actor_id: Optional[int] = None,
    company_id: Optional[int] = None,
    ttl_days: int = DEFAULT_TTL_DAYS,
) -> None:
    """Push a new admin notification payload into Redis."""

    payload = {
        "ts": _now_iso(),
        "type": event_type,
        "title": title,
        "message": message,
        "link": link,
        "actor_id": actor_id,
        "company_id": company_id,
        "ttl_days": ttl_days,
    }
    redis_client.lpush(ADMIN_NOTIF_LIST_KEY, json.dumps(payload))
    redis_client.ltrim(ADMIN_NOTIF_LIST_KEY, 0, MAX_LIST_SIZE - 1)


def list_admin_notifications(limit: int = 20) -> List[Dict[str, Any]]:
    """Return the most recent, non-expired admin notification payloads."""

    raw_items = redis_client.lrange(ADMIN_NOTIF_LIST_KEY, 0, limit - 1) or []
    items: List[Dict[str, Any]] = []
    now = datetime.utcnow()

    for raw in raw_items:
        try:
            obj = json.loads(raw)
        except Exception:  # pragma: no cover - guard against malformed payloads
            continue

        ttl_days = int(obj.get("ttl_days", DEFAULT_TTL_DAYS))
        ts_value = obj.get("ts")
        if ts_value:
            try:
                dt = datetime.fromisoformat(ts_value.replace("Z", ""))
            except Exception:  # pragma: no cover - fallback for invalid timestamps
                dt = now
            if now - dt > timedelta(days=ttl_days):
                continue

        items.append(obj)

    return items


def get_unread_count(user_id: int, sample_limit: int = 50) -> int:
    """Return the number of unread notifications since the user's last seen timestamp."""

    last_seen = redis_client.get(ADMIN_NOTIF_LAST_SEEN_KEY.format(user_id=user_id))
    if not last_seen:
        return len(list_admin_notifications(sample_limit))

    try:
        seen_dt = datetime.fromisoformat(last_seen.replace("Z", ""))
    except Exception:  # pragma: no cover - fallback to counting sample window
        return len(list_admin_notifications(sample_limit))

    unread = 0
    for notification in list_admin_notifications(sample_limit):
        try:
            ts_value = notification["ts"]
            ts = datetime.fromisoformat(ts_value.replace("Z", ""))
        except Exception:  # pragma: no cover - skip malformed timestamps
            continue
        if ts > seen_dt:
            unread += 1

    return unread


def get_notifications_for_user(user_id: int, limit: int = 20) -> list[dict]:
    """
    Retrieve the most recent notifications for a given user.
    Returns a list of serialized notification dicts.
    """

    if not user_id:
        return []

    notifications = (
        Notification.query.filter_by(user_id=user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": n.id,
            "title": n.title or "Notification",
            "message": n.message or "",
            "is_read": getattr(n, "is_read", False),
            "ts": n.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "link": getattr(n, "link", None),
        }
        for n in notifications
    ]


def mark_all_read(user_id: int) -> None:
    """Mark all admin notifications as read for the specified administrator."""

    redis_client.set(ADMIN_NOTIF_LAST_SEEN_KEY.format(user_id=user_id), _now_iso())


__all__ = [
    "queue_notification",
    "broadcast_new_offer",
    "send_admin_broadcast_notifications",
    "send_welcome_notification",
    "ensure_welcome_notification",
    "notify_membership_upgrade",
    "notify_offer_redemption_activity",
    "notify_offer_feedback",
    "fetch_offer_feedback_counts",
    "create_notification_task",
    "broadcast_offer_task",
    "push_admin_notification",
    "list_admin_notifications",
    "get_unread_count",
    "get_notifications_for_user",
    "mark_all_read",
]
