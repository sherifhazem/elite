"""Admin routes for analytics summaries."""

from __future__ import annotations

from datetime import datetime, timezone

from flask import abort, jsonify, request

from app.services.access_control import admin_required
from app.services.analytics_service import (
    active_members_count,
    active_partners_count,
    incentives_applied,
    successful_usages,
    total_usage_attempts,
)
from .. import admin


def _parse_iso8601(value: str | None) -> datetime | None:
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


@admin.route("/analytics/summary", methods=["GET"], endpoint="analytics_summary")
@admin_required
def analytics_summary() -> tuple[dict[str, object], int]:
    """Return analytics summary metrics for the admin dashboard."""

    try:
        date_from = _parse_iso8601(request.args.get("date_from"))
        date_to = _parse_iso8601(request.args.get("date_to"))
    except ValueError:
        abort(400, description="Invalid ISO8601 date_from/date_to parameter.")

    payload = {
        "total_usage_attempts": total_usage_attempts(
            date_from=date_from, date_to=date_to
        ),
        "successful_usages": successful_usages(date_from=date_from, date_to=date_to),
        "incentives_applied": incentives_applied(
            date_from=date_from, date_to=date_to
        ),
        "active_members_count": active_members_count(
            date_from=date_from, date_to=date_to
        ),
        "active_partners_count": active_partners_count(
            date_from=date_from, date_to=date_to
        ),
    }
    return jsonify(payload), 200
