"""Company portal route registrations grouped by domain."""

from .. import company_portal
from ..company_registration_routes import company_bp
from . import (
    routes_dashboard,
    routes_offers,
    routes_registration,
    routes_settings,
    routes_usage_codes,
    routes_communication,
)

__all__ = ["company_bp", "company_portal"]
