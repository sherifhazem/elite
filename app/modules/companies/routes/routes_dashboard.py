"""Entry redirects for the company portal."""

from __future__ import annotations

from flask import redirect, url_for
from app.services.access_control import company_required
from . import company_portal


@company_portal.route("/", endpoint="company_dashboard_redirect")
@company_required
def company_dashboard_redirect() -> str:
    """Redirect root portal requests to the usage codes home view."""

    return redirect(url_for("company_portal.company_usage_codes"))


@company_portal.route("/dashboard", endpoint="company_dashboard_overview")
@company_required
def company_dashboard_overview() -> str:
    """Redirect legacy dashboard visits to the usage codes home view."""

    return redirect(url_for("company_portal.company_usage_codes"))
