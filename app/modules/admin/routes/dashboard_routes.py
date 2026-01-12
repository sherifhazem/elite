"""Admin routes: dashboard overview and admin session controls."""

from __future__ import annotations

from flask import Response, render_template, redirect, url_for, flash, request, abort

from app.services.access_control import admin_required

from .. import admin
from ..services.analytics_summary_service import (
    get_analytics_summary,
    parse_iso8601,
)
from ..services.dashboard_service import get_overview_metrics, process_logout


@admin.route("/logout", endpoint="admin_logout")
@admin_required
def admin_logout() -> Response:
    """تسجيل خروج الأدمن مع مسح الكوكي والجلسة."""

    resp = process_logout()
    flash("تم تسجيل الخروج بنجاح ✅", "info")
    return resp


@admin.route("/", endpoint="dashboard_home")
@admin_required
def dashboard_home() -> str:
    """Render the admin dashboard landing page."""

    metrics = get_overview_metrics()
    date_from_raw = request.args.get("date_from") or ""
    date_to_raw = request.args.get("date_to") or ""

    try:
        date_from = parse_iso8601(date_from_raw)
        date_to = parse_iso8601(date_to_raw)
    except ValueError:
        abort(400, description="Invalid ISO8601 date_from/date_to parameter.")

    analytics_summary = get_analytics_summary(date_from=date_from, date_to=date_to)

    return render_template(
        "admin/dashboard/index.html",
        section_title="Overview",
        active_page="overview",
        total_users=metrics["total_users"],
        total_companies=metrics["total_companies"],
        total_offers=metrics["total_offers"],
        analytics_summary=analytics_summary,
        date_from=date_from_raw,
        date_to=date_to_raw,
    )


@admin.route("/dashboard", endpoint="dashboard_alias")
@admin_required
def dashboard_alias() -> Response:
    """Preserve backwards compatibility for /admin/dashboard links."""

    return redirect(url_for("admin.dashboard_home"))
