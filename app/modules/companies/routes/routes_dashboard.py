"""Dashboard views for the company portal."""

from __future__ import annotations

from datetime import datetime

from flask import redirect, render_template, url_for
from sqlalchemy import func

from app.models import Offer
from app.services.access_control import company_required
from . import company_portal
from app.utils.company_context import _ensure_company, _current_company


@company_portal.route("/", endpoint="company_dashboard_redirect")
@company_required
def company_dashboard_redirect() -> str:
    """Redirect root portal requests to the dashboard overview view."""

    return redirect(url_for("company_portal.company_dashboard_overview"))


@company_portal.route("/dashboard", endpoint="company_dashboard_overview")
@company_required
def company_dashboard_overview() -> str:
    """Render the overview cards and latest redemption activity."""

    company = _current_company()

    active_offers = (
        Offer.query.filter(Offer.company_id == company.id)
        .filter((Offer.valid_until.is_(None)) | (Offer.valid_until >= datetime.utcnow()))
        .count()
    )



    return render_template(
        "companies/dashboard_overview.html",
        company=company,
        active_offers=active_offers,
        total_redeemed=0,
        unique_customers=0,
        last_redemption=None,
        recent_redemptions=[],
    )
