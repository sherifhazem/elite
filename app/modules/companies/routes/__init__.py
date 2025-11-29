"""Company portal route registrations grouped by domain."""

from .. import company_portal

from . import (  # noqa: F401
    routes_dashboard,
    routes_offers,
    routes_redemptions,
    routes_registration,
    routes_settings,
)

__all__ = ["company_portal"]
