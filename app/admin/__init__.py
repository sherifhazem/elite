# ADDED: Admin Communication Center – bulk/group message system (no DB schema change).
"""Admin blueprint package initialization for dashboard routes."""
# This file exposes the admin blueprint for convenient imports.

from .routes import admin_bp

# Import communication routes so they register with the shared blueprint.
from . import routes_communications  # noqa: F401
from . import routes_companies  # noqa: F401

__all__ = ["admin_bp"]
