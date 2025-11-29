"""Admin routes: activity logging views and filters."""

from __future__ import annotations

from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request,
    jsonify,
    abort,
    Response,
)

from app import db
from app.models import User, Company, Offer, ActivityLog
from app.modules.members.services.roles import admin_required

from .. import admin


@admin.route("/activity-log", methods=["GET"], endpoint="activity_log")
@admin_required
def activity_log() -> str:
    """Display admin activity log entries inside Admin Panel."""

    admin_id = request.args.get("admin_id", type=int)
    company_id = request.args.get("company_id", type=int)

    query = ActivityLog.query.order_by(ActivityLog.timestamp.desc())

    if admin_id:
        query = query.filter(ActivityLog.admin_id == admin_id)
    if company_id:
        query = query.filter(ActivityLog.company_id == company_id)

    logs = query.all()
    admins = User.query.filter_by(role="admin").all()

    return render_template(
        "dashboard/activity_log.html",
        logs=logs,
        admins=admins,
        selected_admin=admin_id,
        selected_company=company_id,
    )
