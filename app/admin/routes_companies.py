# -*- coding: utf-8 -*-
"""Admin routes for managing companies (simple and clean)."""

# Use the main admin blueprint already defined in routes.py
from . routes import admin_bp

from flask import render_template, redirect, url_for, flash, request
from app import db
from app.models import Company
from app.services.roles import admin_required
from app.services.mailer import (
    send_company_approval_email,
    send_company_correction_email,
    send_company_suspension_email,
    send_company_reactivation_email,
)

# ==============================
# List Companies
# ==============================
@admin_bp.route("/companies", methods=["GET"])
@admin_required
def list_companies():
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


# ==============================
# View Company Details
# ==============================
@admin_bp.route("/companies/<int:company_id>", methods=["GET"])
@admin_required
def view_company(company_id):
    company = Company.query.get_or_404(company_id)
    return render_template("dashboard/company_details.html", company=company)


# ==============================
# Edit Company
# ==============================
@admin_bp.route("/companies/<int:company_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_company(company_id):
    company = Company.query.get_or_404(company_id)
    if request.method == "POST":
        company.name = request.form.get("name", company.name)
        company.email = request.form.get("email", company.email)
        company.city = request.form.get("city", company.city)
        company.industry = request.form.get("industry", company.industry)
        db.session.commit()
        flash("Company updated successfully.", "success")
        return redirect(url_for("admin.view_company", company_id=company.id))
    return render_template("dashboard/company_edit.html", company=company)


# ==============================
# Delete Company
# ==============================
@admin_bp.route("/companies/<int:company_id>/delete", methods=["POST"])
@admin_required
def delete_company(company_id):
    company = Company.query.get_or_404(company_id)
    db.session.delete(company)
    db.session.commit()
    flash("Company deleted successfully.", "success")
    return redirect(url_for("admin.list_companies"))


# ==============================
# Admin Actions
# ==============================
@admin_bp.route("/companies/<int:company_id>/approve", methods=["POST"])
@admin_required
def approve_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.status = "approved"
    db.session.commit()
    send_company_approval_email(company)
    flash("Company activated successfully.", "success")
    return redirect(url_for("admin.list_companies"))


@admin_bp.route("/companies/<int:company_id>/suspend", methods=["POST"])
@admin_required
def suspend_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.status = "suspended"
    db.session.commit()
    send_company_suspension_email(company)
    flash("Company suspended successfully.", "warning")
    return redirect(url_for("admin.list_companies"))


@admin_bp.route("/companies/<int:company_id>/reactivate", methods=["POST"])
@admin_required
def reactivate_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.status = "approved"
    db.session.commit()
    send_company_reactivation_email(company)
    flash("Company reactivated successfully.", "success")
    return redirect(url_for("admin.list_companies"))
