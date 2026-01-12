"""Admin-facing analytics summary helpers."""

from __future__ import annotations

from datetime import datetime, timezone

from app.services.analytics_service import (
    active_members_count,
    active_partners_count,
    incentives_applied,
    successful_usages,
    total_usage_attempts,
)


def get_analytics_summary(
    *, date_from: datetime | None = None, date_to: datetime | None = None
) -> dict[str, object]:
    """Return analytics summary metrics for the admin dashboard layer."""

    incentives = incentives_applied(date_from=date_from, date_to=date_to)
    summary: dict[str, object] = {
        "total_usage_attempts": total_usage_attempts(
            date_from=date_from, date_to=date_to
        ),
        "successful_usages": successful_usages(
            date_from=date_from, date_to=date_to
        ),
        "incentives_applied": incentives,
        "active_members_count": active_members_count(
            date_from=date_from, date_to=date_to
        ),
        "active_partners_count": active_partners_count(
            date_from=date_from, date_to=date_to
        ),
    }

    incentives_breakdown = {
        key: incentives[key]
        for key in ("first_time", "loyalty")
        if key in incentives
    }
    if incentives_breakdown:
        summary["incentives_applied_breakdown"] = incentives_breakdown

    return summary


def parse_iso8601(value: str | None) -> datetime | None:
    if not value:
        return None

    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError("Expected ISO8601 datetime format.") from exc

    if parsed.tzinfo is not None:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)

    return parsed
