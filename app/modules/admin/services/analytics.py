# LINKED: Shared Offers & Redemptions Integration (no schema changes)
"""Analytics aggregation helpers for the admin reports dashboard."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy import func

from app.core.database import db
from app.models.company import Company
from app.models.offer import Offer
from app.models.user import User
<<<<<<< HEAD
from core.observability.logger import (
    get_service_logger,
    log_service_error,
    log_service_start,
    log_service_step,
    log_service_success,
)

service_logger = get_service_logger(__name__)


def _log(function: str, event: str, message: str, details: Dict[str, object] | None = None, level: str = "INFO") -> None:
    """Internal helper to emit standardized service logs."""

    normalized_level = level.upper()
    if normalized_level == "ERROR" or event in {"soft_failure", "validation_failure"}:
        log_service_error(__name__, function, message, details=details, event=event)
    elif event == "service_start":
        log_service_start(__name__, function, message, details)
    elif event in {"service_complete", "service_success"}:
        log_service_success(__name__, function, message, details=details, event=event)
    else:
        log_service_step(__name__, function, message, details=details, event=event, level=level)
=======
>>>>>>> parent of 29a5adb (Add local observability layer and structured logging (#168))


def _normalize_membership(level: str | None) -> str:
    """Return a normalized membership name recognised by the dashboard."""

    if not level:
        return "Basic"
    normalized = level.strip().title()
    return normalized if normalized in User.MEMBERSHIP_LEVELS else "Basic"


def get_user_summary() -> Dict[str, object]:
    """Return aggregated statistics for users and memberships."""

    total_users = db.session.query(func.count(User.id)).scalar() or 0

    membership_counts: Dict[str, int] = {level: 0 for level in User.MEMBERSHIP_LEVELS}
    for level, count in (
        db.session.query(User.membership_level, func.count(User.id))
        .group_by(User.membership_level)
        .all()
    ):
        membership_counts[_normalize_membership(level)] += int(count or 0)

    last_week = datetime.utcnow() - timedelta(days=7)
    new_users = (
        db.session.query(func.count(User.id))
        .filter(User.joined_at >= last_week)
        .scalar()
        or 0
    )

    return {
        "total_users": int(total_users),
        "new_last_7_days": int(new_users),
        "membership_counts": membership_counts,
    }


def get_company_summary() -> Dict[str, object]:
    """Return aggregated statistics for partner companies."""

    total_companies = db.session.query(func.count(Company.id)).scalar() or 0

    last_month = datetime.utcnow() - timedelta(days=30)
    new_companies = (
        db.session.query(func.count(Company.id))
        .filter(Company.created_at >= last_month)
        .scalar()
        or 0
    )

    return {
        "total_companies": int(total_companies),
        "new_last_30_days": int(new_companies),
    }


def get_offer_summary() -> Dict[str, object]:
    """Return aggregated statistics for offers and discounts."""

    now = datetime.utcnow()

    active_offers = (
        db.session.query(func.count(Offer.id))
        .filter((Offer.valid_until.is_(None)) | (Offer.valid_until >= now))
        .scalar()
        or 0
    )
    expired_offers = (
        db.session.query(func.count(Offer.id))
        .filter(Offer.valid_until.is_not(None), Offer.valid_until < now)
        .scalar()
        or 0
    )

    avg_discount = db.session.query(func.avg(Offer.base_discount)).scalar() or 0.0

    trend_window = now - timedelta(days=90)
    offers_since_window = (
        Offer.query.filter(Offer.created_at >= trend_window)
        .with_entities(Offer.created_at)
        .order_by(Offer.created_at)
        .all()
    )

    weekly_totals: defaultdict[str, int] = defaultdict(int)
    for (created_at,) in offers_since_window:
        if not created_at:
            continue
        start_of_week = (created_at - timedelta(days=created_at.weekday())).date()
        key = start_of_week.isoformat()
        weekly_totals[key] += 1

    trend_data: List[Dict[str, object]] = []
    for week_start in sorted(weekly_totals.keys()):
        trend_data.append({"period_start": week_start, "count": weekly_totals[week_start]})

    latest_offers = [
        {
            "id": offer.id,
            "title": offer.title,
            "company": offer.company.name if offer.company else "-",
            "base_discount": float(offer.base_discount or 0.0),
            "created_at": offer.created_at.isoformat() if offer.created_at else None,
            "valid_until": offer.valid_until.isoformat() if offer.valid_until else None,
        }
        for offer in Offer.query.order_by(Offer.created_at.desc()).limit(5)
    ]

    return {
        "active_offers": int(active_offers),
        "expired_offers": int(expired_offers),
        "average_discount": float(round(avg_discount, 2)),
        "redemption_rate": 0.0,
        "trend": trend_data,
        "latest": latest_offers,
    }


def get_membership_distribution() -> Dict[str, object]:
    """Return pie-chart friendly membership distribution data."""

    counts = get_user_summary()["membership_counts"]  # type: ignore[index]
    labels = list(counts.keys())
    values = [counts[label] for label in labels]
    return {"labels": labels, "values": values}


def get_recent_activity(days: int = 7) -> Dict[str, List[Dict[str, object]]]:
    """Return a chronological list of registrations within the supplied window."""

    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days - 1)

    activity_lookup: defaultdict[str, int] = defaultdict(int)
    for joined_at, count in (
        db.session.query(func.date(User.joined_at), func.count(User.id))
        .filter(User.joined_at >= datetime.combine(start_date, datetime.min.time()))
        .group_by(func.date(User.joined_at))
        .order_by(func.date(User.joined_at))
        .all()
    ):
        key = joined_at.isoformat() if hasattr(joined_at, "isoformat") else str(joined_at)
        activity_lookup[key] = int(count or 0)

    timeline: List[Dict[str, object]] = []
    current = start_date
    while current <= end_date:
        key = current.isoformat()
        timeline.append({"date": key, "registrations": activity_lookup.get(key, 0)})
        current += timedelta(days=1)

    return {"timeline": timeline}
