"""Admin dashboard routes restricted to privileged users."""

from __future__ import annotations

from functools import wraps
from http import HTTPStatus
from typing import Any, Callable, TypeVar

from flask import Blueprint, abort, render_template, request

from ..auth.utils import decode_token
from ..models.user import User

F = TypeVar("F", bound=Callable[..., Any])

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin",
    template_folder="templates",
)


def _extract_bearer_token() -> str | None:
    """Return a bearer token from the Authorization header if present."""

    authorization = request.headers.get("Authorization", "").strip()
    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


def admin_required(func: F) -> F:
    """Decorator ensuring the current request originates from an admin user."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        token = _extract_bearer_token()
        if not token:
            abort(HTTPStatus.UNAUTHORIZED)

        try:
            user_id = decode_token(token)
        except ValueError:
            abort(HTTPStatus.UNAUTHORIZED)

        user = User.query.get(user_id)
        if user is None or not getattr(user, "is_admin", False):
            abort(HTTPStatus.FORBIDDEN)

        return func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


@admin_bp.route("/")
@admin_required
def dashboard_home() -> str:
    """Render the admin dashboard landing page."""

    return render_template("dashboard/index.html", section_title="Overview")


@admin_bp.route("/users")
@admin_required
def dashboard_users() -> str:
    """Render the user management placeholder view."""

    return render_template("dashboard/users.html", section_title="Users")


@admin_bp.route("/companies")
@admin_required
def dashboard_companies() -> str:
    """Render the company management placeholder view."""

    return render_template("dashboard/companies.html", section_title="Companies")


@admin_bp.route("/offers")
@admin_required
def dashboard_offers() -> str:
    """Render the offer management placeholder view."""

    return render_template("dashboard/offers.html", section_title="Offers")
