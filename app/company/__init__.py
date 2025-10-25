"""Company portal package exposing the Flask blueprint for /company pages."""

from flask import Blueprint

company_portal = Blueprint(
    "company_portal",
    __name__,
    url_prefix="/company"
)

from . import routes  # noqa: E402,F401

__all__ = ["company_portal"]
