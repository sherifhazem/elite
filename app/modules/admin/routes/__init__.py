"""Modular admin route package for blueprint registrations."""

from . import (
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

__all__ = [
    "dashboard_routes",
    "users_routes",
    "companies_routes",
    "offers_routes",
    "settings_routes",
    "communications_routes",
    "logs_routes",
    "notifications_routes",
    "reports_routes",
]
