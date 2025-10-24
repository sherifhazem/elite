"""Dedicated admin routes for company detail views."""

from __future__ import annotations

from typing import List

from flask import flash, g, redirect, render_template, request, url_for

from app import app, db
from app.models.activity_log import ActivityLog
from ..models.company import Company
from ..models.offer import Offer
from ..models.redemption import Redemption
from ..services.notifications import push_admin_notification
# ======================================================
# Email Notifications and Admin Permissions
# ======================================================
from app.services.mailer import (
    send_company_approval_email,
    send_company_correction_email,
    send_company_suspension_email,
    send_company_reactivation_email,
)
from app.services.roles import admin_required

from .routes import admin_bp


def log_admin_action(admin, company, action, details=None):
    """Record an administrative action in the activity log."""
    try:
        entry = ActivityLog(
            admin_id=admin.id if admin else 0,
            company_id=company.id,
            action=action,
            details=details or "",
        )
        db.session.add(entry)
        db.session.commit()
        app.logger.info(
            f"📝 {action.title()} | {company.name} by {getattr(admin, 'username', 'Unknown')}"
        )
    except Exception as e:
        app.logger.error(f"❌ Failed to log admin action: {e}")


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
def approve_company(company_id):
    """Approve a pending company application."""
    company = Company.query.get_or_404(company_id)
    company.status = "active"
    db.session.commit()
    log_admin_action(g.current_user, company, "approve")

    try:
        send_company_approval_email(company)
    except Exception as e:
        app.logger.warning(f"Failed to send approval email: {e}")

    flash(f"Company '{company.name}' activated successfully.", "success")
    return redirect(url_for("admin.list_companies", status="active"))


@admin_bp.route("/companies/<int:company_id>/request_correction", methods=["POST"])
@admin_required
def request_correction(company_id):
    """Request data correction or additional info from a company."""
    company = Company.query.get_or_404(company_id)
    notes = request.form.get("admin_notes", "").strip()
    company.admin_notes = notes
    company.status = "correction"
    db.session.commit()
    log_admin_action(g.current_user, company, "request_correction", notes)

    correction_link = url_for(
        "company_portal_bp.complete_registration",
        company_id=company.id,
        _external=True,
    )
    try:
        send_company_correction_email(company, notes, correction_link)
    except Exception as e:
        app.logger.warning(f"Failed to send correction email: {e}")

    flash(f"Correction request sent to '{company.email}'", "warning")
    return redirect(url_for("admin.list_companies", status="correction"))


@admin_bp.route("/companies/<int:company_id>/suspend", methods=["POST"])
@admin_required
def suspend_company(company_id):
    """Suspend a company's account (temporarily disabled)."""
    company = Company.query.get_or_404(company_id)

    # Normalize and update status
    company.status = "suspended"
    db.session.commit()
    log_admin_action(g.current_user, company, "suspend")

    try:
        send_company_suspension_email(company)
    except Exception as e:
        app.logger.warning(f"Failed to send suspension email: {e}")

    flash(f"Company '{company.name}' has been suspended successfully.", "warning")
    return redirect(url_for("admin.list_companies", status="suspended"))


@admin_bp.route("/companies/<int:company_id>/reactivate", methods=["POST"])
@admin_required
def reactivate_company(company_id):
    """Reactivate a previously suspended company."""
    company = Company.query.get_or_404(company_id)

    # Normalize and update status
    company.status = "active"
    db.session.commit()
    log_admin_action(g.current_user, company, "reactivate")

    try:
        send_company_reactivation_email(company)
    except Exception as e:
        app.logger.warning(f"Failed to send reactivation email: {e}")

    flash(f"Company '{company.name}' has been reactivated successfully.", "success")
    return redirect(url_for("admin.list_companies", status="active"))


