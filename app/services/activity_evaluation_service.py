"""Read-only activity evaluation helpers for members and partners."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func

from app.core.database import db
from app.models import ActivityLog
from app.modules.admin.services.admin_settings_service import get_admin_settings


def _get_activity_rules(setting_key: str) -> dict:
    settings = get_admin_settings()
    return settings.get(setting_key, {})


def _window_start(time_window_days: int | None) -> datetime:
    days = int(time_window_days or 0)
    if days < 0:
        days = 0
    return datetime.utcnow() - timedelta(days=days)


def _base_usage_query(window_start: datetime):
    return (
        ActivityLog.query.filter_by(action="usage_code_attempt", result="valid")
        .filter(ActivityLog.created_at >= window_start)
    )


def is_member_active(member_id: int) -> bool:
    """Return True when the member meets the usage activity threshold."""

    rules = _get_activity_rules("member_activity_rules")
    required_usages = int(rules.get("required_usages", 0))
    time_window_days = int(rules.get("time_window_days", 0))

    if required_usages <= 0:
        return False

    window_start = _window_start(time_window_days)
    usage_count = _base_usage_query(window_start).filter_by(member_id=member_id).count()

    return usage_count >= required_usages


def is_partner_active(partner_id: int) -> bool:
    """Return True when the partner meets the usage activity threshold."""

    rules = _get_activity_rules("partner_activity_rules")
    required_usages = int(rules.get("required_usages", 0))
    time_window_days = int(rules.get("time_window_days", 0))
    require_unique_customers = bool(rules.get("require_unique_customers", False))

    if required_usages <= 0:
        return False

    window_start = _window_start(time_window_days)
    base_query = _base_usage_query(window_start).filter_by(partner_id=partner_id)

    if require_unique_customers:
        usage_count = (
            base_query.filter(ActivityLog.member_id.isnot(None))
            .with_entities(func.count(func.distinct(ActivityLog.member_id)))
            .scalar()
            or 0
        )
    else:
        usage_count = base_query.count()

    return usage_count >= required_usages
