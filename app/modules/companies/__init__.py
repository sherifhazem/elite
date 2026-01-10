"""Company portal package exposing the Flask blueprint for /company pages."""

from __future__ import annotations

from flask import Blueprint

company_portal = Blueprint(
    "company_portal",
    __name__,
    url_prefix="/company",
    template_folder="templates/companies",
    static_folder="static",
)

from .routes import (  # noqa: E402,F401
    routes_dashboard,
    routes_offers,
    routes_redemptions,
    routes_registration,
    routes_settings,
    routes_usage_codes,
)

__all__ = ["company_portal"]
