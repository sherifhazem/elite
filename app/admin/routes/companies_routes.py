"""Admin routes: company onboarding, approvals, and lifecycle management."""

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
from app.services.roles import admin_required

from ...services.mailer import (
    send_company_approval_email,
    send_company_correction_email,
    send_company_reactivation_email,
    send_company_suspension_email,
)
from .. import admin


@admin.route("/companies", methods=["GET"], endpoint="list_companies")
@admin_required
def list_companies() -> str:
    """Render a filtered list of companies by status with counts per tab."""

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


@admin.route("/companies/<int:company_id>", methods=["GET"], endpoint="view_company")
@admin_required
def view_company(company_id: int) -> str:
    """Display company details for administrative review."""

    company = Company.query.get_or_404(company_id)
    return render_template("dashboard/company_details.html", company=company)


@admin.route(
    "/companies/<int:company_id>/edit", methods=["GET", "POST"], endpoint="edit_company"
)
@admin_required
def edit_company(company_id: int) -> str:
    """Allow administrators to edit core company attributes."""

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


@admin.route(
    "/companies/<int:company_id>/delete", methods=["POST"], endpoint="delete_company"
)
@admin_required
def delete_company(company_id: int) -> str:
    """Delete a company record and redirect to the listing view."""

    company = Company.query.get_or_404(company_id)
    db.session.delete(company)
    db.session.commit()
    flash("Company deleted successfully.", "success")
    return redirect(url_for("admin.list_companies"))


@admin.route(
    "/companies/<int:company_id>/approve", methods=["POST"], endpoint="approve_company"
)
@admin_required
def approve_company(company_id: int) -> str:
    """Approve a pending company and send the appropriate notification."""

    company = Company.query.get_or_404(company_id)
    company.status = "approved"
    db.session.commit()
    send_company_approval_email(company)
    flash("Company activated successfully.", "success")
    return redirect(url_for("admin.list_companies"))


@admin.route(
    "/companies/<int:company_id>/suspend", methods=["POST"], endpoint="suspend_company"
)
@admin_required
def suspend_company(company_id: int) -> str:
    """Suspend an existing company and notify relevant stakeholders."""

    company = Company.query.get_or_404(company_id)
    company.status = "suspended"
    db.session.commit()
    send_company_suspension_email(company)
    flash("Company suspended successfully.", "warning")
    return redirect(url_for("admin.list_companies"))


@admin.route(
    "/companies/<int:company_id>/reactivate",
    methods=["POST"],
    endpoint="reactivate_company",
)
@admin_required
def reactivate_company(company_id: int) -> str:
    """Reactivate a suspended company and send confirmation."""

    company = Company.query.get_or_404(company_id)
    company.status = "approved"
    db.session.commit()
    send_company_reactivation_email(company)
    flash("Company reactivated successfully.", "success")
    return redirect(url_for("admin.list_companies"))


@admin.route(
    "/companies/<int:company_id>/correction",
    methods=["POST"],
    endpoint="request_company_correction",
)
@admin_required
def request_company_correction(company_id: int) -> str:
    """Move a company to correction status and notify for edits."""

    company = Company.query.get_or_404(company_id)
    company.status = "correction"
    db.session.commit()
    send_company_correction_email(company)
    flash("Company moved to correction status.", "info")
    return redirect(url_for("admin.list_companies"))
