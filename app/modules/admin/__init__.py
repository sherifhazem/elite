"""Admin blueprint initialization and modular route aggregation."""

from flask import Blueprint

admin = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin",
    template_folder="templates",
    static_folder="static",
)

# Register all modular route files
from .routes import (
    dashboard_routes,
    users_routes,
    companies_routes,
    offers_routes,
    settings_routes,
    communications_routes,
    logs_routes,
    notifications_routes,
    reports_routes,
)
