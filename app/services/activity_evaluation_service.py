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


def is_member_active(member_id: int) -> bool:
    """Return True when the member meets the usage activity threshold."""

    rules = _get_activity_rules("member_activity_rules")
    required_usages = int(rules.get("required_usages", 0))
    time_window_days = int(rules.get("time_window_days", 0))

    window_start = _window_start(time_window_days)
    usage_count = (
        ActivityLog.query.filter_by(
            action="usage_code_attempt",
            result="valid",
            member_id=member_id,
        )
        .filter(ActivityLog.created_at >= window_start)
        .count()
    )

    return usage_count >= required_usages


def is_partner_active(partner_id: int) -> bool:
    """Return True when the partner meets the usage activity threshold."""

    rules = _get_activity_rules("partner_activity_rules")
    required_usages = int(rules.get("required_usages", 0))
    time_window_days = int(rules.get("time_window_days", 0))
    require_unique_customers = bool(rules.get("require_unique_customers", False))

    window_start = _window_start(time_window_days)
    base_query = ActivityLog.query.filter_by(
        action="usage_code_attempt",
        result="valid",
        partner_id=partner_id,
    ).filter(ActivityLog.created_at >= window_start)

    if require_unique_customers:
        usage_count = (
            db.session.query(func.count(func.distinct(ActivityLog.member_id)))
            .filter(ActivityLog.member_id.isnot(None))
            .filter(ActivityLog.action == "usage_code_attempt")
            .filter(ActivityLog.result == "valid")
            .filter(ActivityLog.partner_id == partner_id)
            .filter(ActivityLog.created_at >= window_start)
            .scalar()
            or 0
        )
    else:
        usage_count = base_query.count()

    return usage_count >= required_usages
