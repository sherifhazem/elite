"""Company portal route registrations grouped by domain."""

from .. import company_portal
from ..company_registration_routes import company_bp

from . import (  # noqa: F401
    routes_dashboard,
    routes_offers,
    routes_redemptions,
    routes_registration,
    routes_settings,
)

__all__ = ["company_bp", "company_portal"]
