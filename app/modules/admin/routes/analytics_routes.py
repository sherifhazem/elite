"""Admin routes for analytics summaries."""

from __future__ import annotations

import csv
import json
from io import StringIO
from datetime import datetime

from flask import abort, jsonify, request, Response, g

from app.core.database import db
from app.models import ActivityLog
from app.services.access_control import admin_required
from ..services.analytics_summary_service import (
    get_analytics_summary,
    parse_iso8601,
)
from .. import admin


@admin.route("/analytics/summary", methods=["GET"], endpoint="analytics_summary")
@admin_required
def analytics_summary() -> tuple[dict[str, object], int]:
    """Return analytics summary metrics for the admin dashboard."""

    try:
        date_from = parse_iso8601(request.args.get("date_from"))
        date_to = parse_iso8601(request.args.get("date_to"))
    except ValueError:
        abort(400, description="Invalid ISO8601 date_from/date_to parameter.")

    payload = get_analytics_summary(date_from=date_from, date_to=date_to)
    return jsonify(payload), 200


@admin.route(
    "/analytics/summary/export", methods=["GET"], endpoint="analytics_summary_export"
)
@admin_required
def analytics_summary_export() -> Response:
    """Export analytics summary metrics as CSV."""

    try:
        date_from = parse_iso8601(request.args.get("date_from"))
        date_to = parse_iso8601(request.args.get("date_to"))
    except ValueError:
        abort(400, description="Invalid ISO8601 date_from/date_to parameter.")

    summary = get_analytics_summary(date_from=date_from, date_to=date_to)
    filename = "analytics-summary.csv"
    admin_id = getattr(getattr(g, "current_user", None), "id", None)
    created_at = datetime.utcnow()
    log_entry = ActivityLog(
        admin_id=admin_id,
        action="analytics_export",
        details=json.dumps(
            {
                "admin_id": admin_id,
                "date_from": date_from.isoformat() if date_from else None,
                "date_to": date_to.isoformat() if date_to else None,
                "filename": filename,
            }
        ),
        created_at=created_at,
        timestamp=created_at,
    )
    db.session.add(log_entry)
    db.session.commit()
    incentives = summary.get("incentives_applied") or {}
    breakdown = summary.get("incentives_applied_breakdown") or {}
    total_incentives = sum(incentives.values()) if incentives else 0

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "date_from",
            "date_to",
            "total_usage_attempts",
            "successful_usages",
            "incentives_applied_total",
            "incentives_applied_first_time",
            "incentives_applied_loyalty",
            "active_members_count",
            "active_partners_count",
        ]
    )
    writer.writerow(
        [
            date_from.isoformat() if date_from else "",
            date_to.isoformat() if date_to else "",
            summary.get("total_usage_attempts", 0),
            summary.get("successful_usages", 0),
            total_incentives,
            breakdown.get("first_time", 0),
            breakdown.get("loyalty", 0),
            summary.get("active_members_count", 0),
            summary.get("active_partners_count", 0),
        ]
    )

    response = Response(buffer.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response
