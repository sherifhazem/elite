"""Admin routes: company onboarding, approvals, and lifecycle management."""

from __future__ import annotations

from flask import flash, redirect, render_template, request, url_for

from app.services.access_control import admin_required

from .. import admin
from ..services.company_management_service import (
    approve_company as approve_company_record,
    delete_company as delete_company_record,
    fetch_companies_by_status,
    get_company,
    reactivate_company as reactivate_company_record,
    request_correction as request_company_correction_record,
    suspend_company as suspend_company_record,
    update_company,
)


@admin.route("/companies", methods=["GET"], endpoint="list_companies")
@admin_required
def list_companies() -> str:
    """Render a filtered list of companies by status with counts per tab."""

    status = request.args.get("status", "pending").lower()
    companies, status_counts = fetch_companies_by_status(status)
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

    company = get_company(company_id)
    return render_template("dashboard/company_details.html", company=company)


@admin.route(
    "/companies/<int:company_id>/edit", methods=["GET", "POST"], endpoint="edit_company"
)
@admin_required
def edit_company(company_id: int) -> str:
    """Allow administrators to edit core company attributes."""

    company = get_company(company_id)
    if request.method == "POST":
        update_company(
            company,
            {
                "name": request.form.get("name", company.name),
                "email": request.form.get("email", company.email),
                "city": request.form.get("city", company.city),
                "industry": request.form.get("industry", company.industry),
            },
        )
        flash("Company updated successfully.", "success")
        return redirect(url_for("admin.view_company", company_id=company.id))
    return render_template("dashboard/company_edit.html", company=company)


@admin.route(
    "/companies/<int:company_id>/delete", methods=["POST"], endpoint="delete_company"
)
@admin_required
def delete_company(company_id: int) -> str:
    """Delete a company record and redirect to the listing view."""

    company = get_company(company_id)
    delete_company_record(company)
    flash("Company deleted successfully.", "success")
    return redirect(url_for("admin.list_companies"))


@admin.route(
    "/companies/<int:company_id>/approve", methods=["POST"], endpoint="approve_company"
)
@admin_required
def approve_company(company_id: int) -> str:
    """Approve a pending company and send the appropriate notification."""

    company = get_company(company_id)
    approve_company_record(company)
    flash("Company activated successfully.", "success")
    return redirect(url_for("admin.list_companies"))


@admin.route(
    "/companies/<int:company_id>/suspend", methods=["POST"], endpoint="suspend_company"
)
@admin_required
def suspend_company(company_id: int) -> str:
    """Suspend an existing company and notify relevant stakeholders."""

    company = get_company(company_id)
    suspend_company_record(company)
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

    company = get_company(company_id)
    reactivate_company_record(company)
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

    company = get_company(company_id)
    request_company_correction_record(company)
    flash("Company moved to correction status.", "info")
    return redirect(url_for("admin.list_companies"))
