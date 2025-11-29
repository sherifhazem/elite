# LINKED: Fixed admin permission logic and restored Site Settings visibility for Admin and Superadmin roles.
# Ensured correct decorator checks and sidebar rendering consistency.
"""Utility helpers implementing the role and permission system."""

from __future__ import annotations

from functools import wraps
from http import HTTPStatus
from typing import Callable, Iterable, Optional, Protocol

from flask import abort, flash, g, redirect, request, url_for
from flask_login import current_user as flask_current_user
from sqlalchemy import func

from app.modules.members.auth.utils import get_user_from_token
from core.observability.logger import (
    get_service_logger,
    log_service_error,
    log_service_start,
    log_service_step,
    log_service_success,
)

# Mapping of role requirements to the set of roles allowed to satisfy them.
ROLE_ACCESS_MATRIX = {
    "member": {"member", "company", "admin", "superadmin"},
    "company": {"company", "superadmin"},
    "admin": {"admin", "superadmin"},
    "superadmin": {"superadmin"},
}

# Default permission-to-role mapping used by can_access.
PERMISSION_ROLE_MATRIX = {
    "manage_users": {"admin", "superadmin"},
    "manage_roles": {"superadmin"},
    "delete_users": {"superadmin"},
    "view_reports": {"admin", "superadmin"},
    "manage_offers": {"company", "admin", "superadmin"},
}


service_logger = get_service_logger(__name__)


def _log(function: str, event: str, message: str, details: dict | None = None, level: str = "INFO") -> None:
    """Emit standardized observability events for member role services."""

    normalized_level = level.upper()
    if normalized_level == "ERROR" or event in {"soft_failure", "validation_failure"}:
        log_service_error(__name__, function, message, details=details, event=event)
    elif event == "service_start":
        log_service_start(__name__, function, message, details)
    elif event in {"service_complete", "service_success"}:
        log_service_success(__name__, function, message, details=details, event=event)
    else:
        log_service_step(
            __name__,
            function,
            message,
            details=details,
            event=event,
            level=level,
        )


class SupportsRole(Protocol):
    """Structural protocol describing user objects used for role checks."""

    normalized_role: str
    is_active: bool

    def has_role(self, required_role: str) -> bool:
        """Return True when the user matches the required role constraint."""


def _extract_token() -> Optional[str]:
    """Return a JWT token from Authorization header or cookie when provided."""

    _log("_extract_token", "service_start", "Extracting token from request")
    authorization = request.headers.get("Authorization", "").strip()
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() == "bearer" and token:
        _log("_extract_token", "service_checkpoint", "Bearer token detected")
        return token

    cookie_token = request.cookies.get("elite_token")
    if cookie_token:
        _log("_extract_token", "service_checkpoint", "Token extracted from cookie")
        return cookie_token
    _log("_extract_token", "service_complete", "No token found in request")
    return None


def resolve_user_from_request():
    """Return the authenticated user object for the current request if available."""

    _log("resolve_user_from_request", "service_start", "Resolving user from incoming request")
    # First prefer explicit bearer tokens to support API and SPA use-cases.
    token = _extract_token()
    if token:
        user = get_user_from_token(token)
        if user is not None:
            _log(
                "resolve_user_from_request",
                "validation_success",
                "User resolved from bearer token",
                {"user_id": getattr(user, "id", None)},
            )
            return user

    # Fall back to Flask-Login's session-based user when available.
    if getattr(flask_current_user, "is_authenticated", False):
        _log(
            "resolve_user_from_request",
            "service_checkpoint",
            "Resolved user from Flask-Login session",
            {"user_id": getattr(flask_current_user, "id", None)},
        )
        return flask_current_user

    _log("resolve_user_from_request", "soft_failure", "No authenticated user found", level="WARNING")
    return None


def has_role(user: Optional[SupportsRole], role_name: str) -> bool:
    """Return True if the provided user holds (or supersedes) the role requirement."""

    _log("has_role", "service_start", "Checking role access", {"role": role_name, "user_id": getattr(user, "id", None)})
    if user is None or not getattr(user, "is_active", False):
        _log("has_role", "soft_failure", "Inactive or missing user", {"role": role_name}, level="WARNING")
        return False

    if hasattr(user, "has_role") and callable(getattr(user, "has_role")):
        return bool(user.has_role(role_name))

    normalized = (role_name or "member").strip().lower()
    allowed_roles = ROLE_ACCESS_MATRIX.get(normalized, {normalized})
    user_role = getattr(user, "normalized_role", None)
    if callable(user_role):  # pragma: no cover - defensive for unconventional objects
        user_role = user_role()
    if not user_role:
        user_role = getattr(user, "role", "member")
    result = str(user_role).strip().lower() in allowed_roles
    _log(
        "has_role",
        "service_complete",
        "Role check evaluated",
        {"required_role": role_name, "user_role": user_role, "allowed": result},
    )
    return result


def require_role(role_name: str) -> Callable:
    """Decorator enforcing that the current request user has the specified role."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = getattr(g, "current_user", None)
            if user is None or not getattr(user, "is_authenticated", False):
                if getattr(flask_current_user, "is_authenticated", False):
                    user = flask_current_user
            if user is None:
                user = resolve_user_from_request()

            if user is None:
                abort(HTTPStatus.UNAUTHORIZED)
            if not getattr(user, "is_active", False):
                abort(HTTPStatus.FORBIDDEN)
            if not has_role(user, role_name):
                abort(HTTPStatus.FORBIDDEN)
            g.current_user = user
            return func(*args, **kwargs)

        return wrapper

    return decorator


def admin_required(view_func: Callable) -> Callable:
    """Decorator enforcing admin (or higher) access with user-friendly redirects."""

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user = getattr(g, "current_user", None)
        if user is None or not getattr(user, "is_authenticated", False):
            if getattr(flask_current_user, "is_authenticated", False):
                user = flask_current_user

        if user is None:
            flash("يُسمح بالوصول للمشرفين فقط", "warning")
            return redirect(url_for("auth.login"))

        if not getattr(user, "is_active", False):
            abort(HTTPStatus.FORBIDDEN)

        if not has_role(user, "admin"):
            abort(HTTPStatus.FORBIDDEN)

        g.current_user = user
        return view_func(*args, **kwargs)

    return wrapper


def can_access(user: Optional[SupportsRole], permission: str) -> bool:
    """Return True when a user can access a named permission or feature."""

    _log(
        "can_access",
        "service_start",
        "Evaluating permission",
        {"permission": permission, "user_id": getattr(user, "id", None)},
    )
    if user is None or not getattr(user, "is_active", False):
        _log("can_access", "soft_failure", "Inactive or missing user", {"permission": permission}, level="WARNING")
        return False

    normalized = (permission or "").strip().lower()
    if not normalized:
        return False

    allowed_roles = PERMISSION_ROLE_MATRIX.get(normalized)
    if allowed_roles and getattr(user, "normalized_role", "member") in allowed_roles:
        _log(
            "can_access",
            "validation_success",
            "Permission granted via role matrix",
            {"permission": permission, "role": getattr(user, "normalized_role", None)},
        )
        return True

    from app.models.permission import Permission

    query = user.permissions if hasattr(user, "permissions") else None
    if query is not None:
        result = (
            query.filter(func.lower(Permission.name) == normalized)
            .with_entities(Permission.id)
            .limit(1)
            .count()
            > 0
        )
        _log(
            "can_access",
            "service_complete",
            "Permission check resolved",
            {"permission": permission, "allowed": result},
        )
        return result
    _log(
        "can_access",
        "soft_failure",
        "Permissions relationship missing on user",
        {"permission": permission},
        level="WARNING",
    )
    return False


def assign_permissions(user, permissions: Iterable[str]) -> None:
    """Utility helper to bulk assign permissions to a user and commit changes."""

    if user is None:
        return
    from app.core.database import db

    user.grant_permissions(permissions)
    db.session.commit()
    _log(
        "assign_permissions",
        "db_write_success",
        "Permissions assigned to user",
        {"user_id": getattr(user, "id", None), "permissions": list(permissions)},
    )


__all__ = [
    "ROLE_ACCESS_MATRIX",
    "PERMISSION_ROLE_MATRIX",
    "has_role",
    "require_role",
    "admin_required",
    "can_access",
    "resolve_user_from_request",
    "assign_permissions",
]
