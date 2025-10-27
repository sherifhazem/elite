"""Company portal package exposing the Flask blueprint for /company pages."""

from __future__ import annotations

import os

from flask import Blueprint
from jinja2 import ChoiceLoader, FileSystemLoader, PrefixLoader

company_portal = Blueprint(
    "company_portal",
    __name__,
    url_prefix="/company",
    template_folder="templates",
)

_template_root = os.path.join(os.path.dirname(__file__), "templates")

company_portal.jinja_loader = ChoiceLoader(
    [
        PrefixLoader({"company": FileSystemLoader(_template_root)}),
        FileSystemLoader(_template_root),
    ]
)

from .routes import (  # noqa: E402,F401
    routes_dashboard,
    routes_offers,
    routes_redemptions,
    routes_registration,
    routes_settings,
)

__all__ = ["company_portal"]
