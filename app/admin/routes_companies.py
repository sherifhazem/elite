# -*- coding: utf-8 -*-
"""Admin routes for managing companies (clean and simplified)."""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models import Company
from app.services.mailer import (
    send_company_approval_email,
    send_company_correction_email,
    send_company_suspension_email,
    send_company_reactivation_email,
)
from app.services.roles import admin_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/companies", methods=["GET"])
@admin_required
def list_companies():
    """Display all companies filtered by status."""
    status = request.args.get("status", "pending").lower()
    companies = Company.query.filter_by(status=status).all()
    status_counts = {
        "pending": Company.query.filter_by(status="pending").count(),
        "approved": Company.query.filter_by(status="approved").count(),
        "suspended": Company.query.filter_by(status="suspended").count(),
        "correction": Company.query.filter_by(status="correction").count(),
    }
    return render_template(
        "dashboard/companies.html",
        companies=companies,
        active_tab=status,
        status_counts=status_counts,
    )


@admin_bp.route("/companies/<int:company_id>", methods=["GET"])
@admin_required
def view_company(company_id):
    """Show full company details."""
    company = Company.query.get_or_404(company_id)
    return render_template("dashboard/company_details.html", company=company)

