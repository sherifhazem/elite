"""Dedicated admin routes for company detail views."""

from __future__ import annotations

from typing import List, Optional

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user

from .. import db
from ..models.company import Company
from ..models.offer import Offer
from ..models.redemption import Redemption
from ..models.activity_log import ActivityLog
from ..services.notifications import push_admin_notification
from ..services.roles import admin_required
from ..services.mailer import (
    send_company_approval_email,
    send_company_correction_email,
    send_company_suspension_email,
    send_company_reactivation_email,
)
from .routes import admin_bp


def log_company_activity(
    company_id: int, admin_id: Optional[int], action: str, notes: Optional[str] = None
) -> None:
    """Persist an activity log entry for a company."""

    entry = ActivityLog(
        company_id=company_id,
        admin_id=admin_id,
        action=action,
        notes=notes,
    )
    db.session.add(entry)
    db.session.commit()


@admin_bp.route("/companies/<int:company_id>", methods=["GET"])
@admin_required
def view_company_details(company_id: int) -> str:
    """Display full details and management actions for a specific company."""

    company = Company.query.get_or_404(company_id)

    preferences = company.notification_settings()
    owner = getattr(company, "owner", None)

    contact_email = getattr(owner, "email", None) or getattr(company, "email", None)
    contact_phone = preferences.get("contact_phone") or getattr(company, "contact_number", None)
    city = preferences.get("city") or getattr(company, "city", None)
    industry = preferences.get("industry") or getattr(company, "industry", None)

    offers: List[Offer] = (
        Offer.query.filter_by(company_id=company.id)
        .order_by(Offer.created_at.desc())
        .all()
    )
    redemptions: List[Redemption] = (
        Redemption.query.filter_by(company_id=company.id)
        .order_by(Redemption.created_at.desc())
        .all()
    )

    return render_template(
        "dashboard/company_details.html",
        company=company,
        offers=offers,
        redemptions=redemptions,
        contact_email=contact_email,
        contact_phone=contact_phone,
        company_city=city,
        company_industry=industry,
    )


@admin_bp.route("/companies/<int:company_id>/approve", methods=["POST"])
@admin_required
def approve_company(company_id: int):
    company = Company.query.get_or_404(company_id)
    company.set_status("approved")
    if company.owner:
        company.owner.is_active = True
    db.session.commit()

    log_company_activity(
        company.id,
        getattr(current_user, "id", None),
        "Approved",
        "Company approved by admin.",
    )

    push_admin_notification(
        event_type="company.approved",
        title="Company Approved",
        message=f"'{company.name}' has been approved.",
        link=f"/admin/companies/{company.id}",
        company_id=company.id,
        actor_id=getattr(current_user, "id", None),
    )

    send_company_approval_email(company)

    flash(f"Company '{company.name}' approved successfully.", "success")
    return redirect(url_for("admin.list_companies"))


@admin_bp.route("/companies/<int:company_id>/request_correction", methods=["POST"])
@admin_required
def request_correction(company_id: int):
    company = Company.query.get_or_404(company_id)
    notes = request.form.get("admin_notes", "").strip()
    company.admin_notes = notes
    company.set_status("correction")
    db.session.commit()

    log_company_activity(
        company.id,
        getattr(current_user, "id", None),
        "Correction Requested",
        notes or None,
    )

    push_admin_notification(
        event_type="company.correction",
        title="Correction Requested",
        message=f"Correction requested for '{company.name}'.",
        link=f"/admin/companies/{company.id}",
        company_id=company.id,
        actor_id=getattr(current_user, "id", None),
    )

    correction_link = f"{request.url_root}company/complete_registration/{company.id}"
    send_company_correction_email(company, notes, correction_link)

    contact_email = (
        getattr(getattr(company, "owner", None), "email", None)
        or getattr(company, "email", None)
        or "company contact"
    )
    flash(f"Correction request sent to '{contact_email}'", "warning")
    return redirect(url_for("admin.list_companies"))


@admin_bp.route("/companies/<int:company_id>/suspend", methods=["POST"])
@admin_required
def suspend_company(company_id: int):
    company = Company.query.get_or_404(company_id)
    company.set_status("suspended")
    company.admin_notes = request.form.get("admin_notes", "").strip()
    db.session.commit()

    log_company_activity(
        company.id,
        getattr(current_user, "id", None),
        "Suspended",
        company.admin_notes or None,
    )

    push_admin_notification(
        event_type="company.suspended",
        title="Company Suspended",
        message=f"'{company.name}' has been suspended.",
        link=f"/admin/companies/{company.id}",
        company_id=company.id,
        actor_id=getattr(current_user, "id", None),
    )

    send_company_suspension_email(company)

    flash(f"Company '{company.name}' has been suspended.", "danger")
    return redirect(url_for("admin.list_companies"))


@admin_bp.route("/companies/<int:company_id>/reactivate", methods=["POST"])
@admin_required
def reactivate_company(company_id: int):
    company = Company.query.get_or_404(company_id)
    company.set_status("approved")
    db.session.commit()

    log_company_activity(
        company.id,
        getattr(current_user, "id", None),
        "Reactivated",
        None,
    )

    push_admin_notification(
        event_type="company.reactivated",
        title="Company Reactivated",
        message=f"'{company.name}' has been reactivated.",
        link=f"/admin/companies/{company.id}",
        company_id=company.id,
        actor_id=getattr(current_user, "id", None),
    )

    send_company_reactivation_email(company)

    flash(f"Company '{company.name}' reactivated successfully.", "success")
    return redirect(url_for("admin.list_companies"))
