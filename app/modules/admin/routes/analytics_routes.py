"""Admin routes for analytics summaries."""

from __future__ import annotations

from flask import abort, jsonify, request

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
