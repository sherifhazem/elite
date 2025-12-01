"""Business logic for admin dashboard and session flows."""

from __future__ import annotations

from flask import Response, make_response, redirect, session, url_for
from flask_login import logout_user

from app.core.database import db
from app.models import Company, Offer, User


def process_logout() -> Response:
    """Handle the full admin logout workflow and return a redirect response."""

    logout_user()
    session.clear()

    response = make_response(redirect(url_for("auth.login")))
    response.delete_cookie("elite_token", path="/")
    response.headers["Clear-Site-Data"] = '"storage"'
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


def get_overview_metrics() -> dict[str, int]:
    """Return aggregate counts for the admin dashboard summary cards."""

    total_users = User.query.count()
    total_companies = (
        db.session.query(User.company_id)
        .filter(User.company_id.isnot(None))
        .distinct()
        .count()
    )
    total_offers = Offer.query.count()
    return {
        "total_users": total_users,
        "total_companies": total_companies,
        "total_offers": total_offers,
    }
