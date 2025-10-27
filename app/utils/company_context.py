"""Utility functions for resolving the current company context for routes and services."""
from http import HTTPStatus

from flask import abort, g

from .. import db
from ..models import Company


def _ensure_company(user) -> Company:
    """Return the company object for the given user or raise appropriate HTTP errors.
    This helper can be safely reused inside both routes and service layers."""
    if user is None:
        abort(HTTPStatus.UNAUTHORIZED)

    company = getattr(user, "company", None)
    if company is None and getattr(user, "company_id", None):
        company = Company.query.get(user.company_id)

    # fallback: search by owner
    if company is None:
        company = Company.query.filter_by(owner_user_id=user.id).first()

    if company is None:
        abort(HTTPStatus.FORBIDDEN)

    # auto-assign owner if missing
    if company.owner_user_id is None:
        company.owner_user_id = user.id
        db.session.commit()

    return company


def _current_company() -> Company:
    """Return the company linked to the current Flask context user (g.current_user)."""
    user = getattr(g, "current_user", None)
    return _ensure_company(user)
