"""Dedicated admin routes for company detail views."""

from __future__ import annotations

from typing import List, Optional

from flask import render_template

from .. import db
from ..models.company import Company
from ..models.offer import Offer
from ..models.redemption import Redemption
from ..models.activity_log import ActivityLog
from ..services.roles import admin_required
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
