# -*- coding: utf-8 -*-
"""Blueprint route to display and filter admin activity log."""

from flask import Blueprint, render_template, request
from app import db
from app.models.activity_log import ActivityLog
from app.models.user import User
from app.models.company import Company
from app.services.roles import admin_required

activity_log_bp = Blueprint("activity_log_bp", __name__, url_prefix="/admin")


@activity_log_bp.route("/activity_log")
@admin_required
def activity_log():
    """Display all admin actions with optional filters."""
    admin_id = request.args.get("admin_id", type=int)
    company_id = request.args.get("company_id", type=int)

    query = ActivityLog.query.order_by(ActivityLog.timestamp.desc())

    if admin_id:
        query = query.filter(ActivityLog.admin_id == admin_id)
    if company_id:
        query = query.filter(ActivityLog.company_id == company_id)

    logs = query.all()
    admins = User.query.filter_by(role="admin").all()
    companies = Company.query.order_by(Company.name.asc()).all()

    return render_template(
        "dashboard/activity_log.html",
        logs=logs,
        admins=admins,
        companies=companies,
        selected_admin=admin_id,
        selected_company=company_id,
    )
