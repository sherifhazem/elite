"""Dedicated admin routes for company detail views."""

from __future__ import annotations

from typing import List

from flask import render_template

from ..models.company import Company
from ..models.offer import Offer
from ..models.redemption import Redemption
from ..services.roles import admin_required
from .routes import admin_bp


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

    activity_log = []
    for offer in offers:
        if offer.created_at:
            activity_log.append(
                {
                    "timestamp": offer.created_at,
                    "label": f"Offer created: {offer.title}",
                    "type": "offer",
                }
            )
    for redemption in redemptions:
        if redemption.created_at:
            user_obj = getattr(redemption, "user", None)
            user_name = (
                getattr(user_obj, "name", None)
                or getattr(user_obj, "username", None)
                or getattr(user_obj, "email", None)
            )
            offer_title = getattr(getattr(redemption, "offer", None), "title", None)
            details = []
            if user_name:
                details.append(user_name)
            if offer_title:
                details.append(offer_title)
            detail_text = " • ".join(details) if details else "Redemption activity recorded"
            activity_log.append(
                {
                    "timestamp": redemption.created_at,
                    "label": f"Redemption created: {detail_text}",
                    "type": "redemption",
                }
            )

    activity_log.sort(key=lambda item: item["timestamp"], reverse=True)

    return render_template(
        "dashboard/company_details.html",
        company=company,
        offers=offers,
        redemptions=redemptions,
        activity_log=activity_log,
        contact_email=contact_email,
        contact_phone=contact_phone,
        company_city=city,
        company_industry=industry,
    )
