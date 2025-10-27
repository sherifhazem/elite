"""Helper utilities for company portal routes."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from flask import abort, g

from ... import db
from ...models import Company

if TYPE_CHECKING:  # pragma: no cover - hints only
    from ...models import User  # noqa: F401


def _ensure_company(user) -> Company:
    if user is None:
        abort(HTTPStatus.UNAUTHORIZED)

    company = getattr(user, "company", None)
    if company is None and getattr(user, "company_id", None):
        company = Company.query.get(user.company_id)

    if company is None:
        company = Company.query.filter(Company.owner_user_id == user.id).first()

    if company is None:
        abort(HTTPStatus.FORBIDDEN)

    if company.owner_user_id is None:
        company.owner_user_id = user.id
        db.session.commit()

    return company


def _current_company() -> Company:
    user = getattr(g, "current_user", None)
    return _ensure_company(user)


__all__ = ["_ensure_company", "_current_company"]
