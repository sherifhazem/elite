"""Read-only analytics queries for operational metrics."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Iterable

from sqlalchemy import func
from sqlalchemy.orm import Query

from app.core.database import db
from app.models import ActivityLog
from app.modules.admin.services.admin_settings_service import get_admin_settings


def _apply_date_range(
    query: Query, *, date_from: datetime | None, date_to: datetime | None
) -> Query:
    if date_from is not None:
        query = query.filter(ActivityLog.created_at >= date_from)
    if date_to is not None:
        query = query.filter(ActivityLog.created_at <= date_to)
    return query


def total_usage_attempts(
    *, date_from: datetime | None = None, date_to: datetime | None = None
) -> int:
    """Return total usage verification attempts within an optional date range."""

    query = ActivityLog.query.filter_by(action="usage_code_attempt")
    query = _apply_date_range(query, date_from=date_from, date_to=date_to)
    return int(query.count())


def successful_usages(
    *, date_from: datetime | None = None, date_to: datetime | None = None
) -> int:
    """Return the count of successful usage attempts (result="valid")."""

    query = ActivityLog.query.filter_by(action="usage_code_attempt", result="valid")
    query = _apply_date_range(query, date_from=date_from, date_to=date_to)
    return int(query.count())


def incentives_applied(
    *, date_from: datetime | None = None, date_to: datetime | None = None
) -> Dict[str, int]:
    """Return counts of applied incentives grouped by incentive type."""

    query = ActivityLog.query.filter_by(action="incentive_applied")
    query = _apply_date_range(query, date_from=date_from, date_to=date_to)
    results: Iterable[tuple[str | None, int]] = (
        query.with_entities(ActivityLog.result, func.count(ActivityLog.id))
        .group_by(ActivityLog.result)
        .all()
    )
    return {str(result): int(count or 0) for result, count in results if result}


def _usage_window_start(time_window_days: int | None) -> datetime:
    days = int(time_window_days or 0)
    if days < 0:
        days = 0
    return datetime.utcnow() - timedelta(days=days)


def active_members_count(
    *, date_from: datetime | None = None, date_to: datetime | None = None
) -> int:
    """Return the number of members meeting the active usage rules."""

    rules = get_admin_settings().get("member_activity_rules", {})
    required_usages = int(rules.get("required_usages", 0))
    time_window_days = int(rules.get("time_window_days", 0))

    if required_usages <= 0:
        return 0

    window_start = _usage_window_start(time_window_days)
    query = ActivityLog.query.filter_by(action="usage_code_attempt", result="valid")
    query = query.filter(ActivityLog.created_at >= window_start)
    query = query.filter(ActivityLog.member_id.isnot(None))
    query = _apply_date_range(query, date_from=date_from, date_to=date_to)

    active_members_subquery = (
        query.with_entities(ActivityLog.member_id)
        .group_by(ActivityLog.member_id)
        .having(func.count(ActivityLog.id) >= required_usages)
        .subquery()
    )

    count = db.session.query(func.count()).select_from(active_members_subquery).scalar()
    return int(count or 0)


def active_partners_count(
    *, date_from: datetime | None = None, date_to: datetime | None = None
) -> int:
    """Return the number of partners meeting the active usage rules."""

    rules = get_admin_settings().get("partner_activity_rules", {})
    required_usages = int(rules.get("required_usages", 0))
    time_window_days = int(rules.get("time_window_days", 0))
    require_unique_customers = bool(rules.get("require_unique_customers", False))

    if required_usages <= 0:
        return 0

    window_start = _usage_window_start(time_window_days)
    query = ActivityLog.query.filter_by(action="usage_code_attempt", result="valid")
    query = query.filter(ActivityLog.created_at >= window_start)
    query = query.filter(ActivityLog.partner_id.isnot(None))
    query = _apply_date_range(query, date_from=date_from, date_to=date_to)

    if require_unique_customers:
        query = query.filter(ActivityLog.member_id.isnot(None))
        count_expr = func.count(func.distinct(ActivityLog.member_id))
    else:
        count_expr = func.count(ActivityLog.id)

    active_partners_subquery = (
        query.with_entities(ActivityLog.partner_id)
        .group_by(ActivityLog.partner_id)
        .having(count_expr >= required_usages)
        .subquery()
    )

    count = db.session.query(func.count()).select_from(active_partners_subquery).scalar()
    return int(count or 0)


__all__ = [
    "total_usage_attempts",
    "successful_usages",
    "incentives_applied",
    "active_members_count",
    "active_partners_count",
]
