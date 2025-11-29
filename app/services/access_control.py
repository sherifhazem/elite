"""Shared access-control utilities reusable across all modules."""

from __future__ import annotations

from importlib import import_module
from typing import Any


def _member_roles() -> Any:
    """Lazily import the member roles module to avoid circular imports."""

    return import_module("app.modules.members.services.roles")


def _get_attr(name: str):
    """Return an attribute from the member roles module when available."""

    return getattr(_member_roles(), name)


ROLE_ACCESS_MATRIX = _get_attr("ROLE_ACCESS_MATRIX")
PERMISSION_ROLE_MATRIX = _get_attr("PERMISSION_ROLE_MATRIX")
resolve_user_from_request = _get_attr("resolve_user_from_request")
require_role = _get_attr("require_role")
admin_required = _get_attr("admin_required")
has_role = _get_attr("has_role")
can_access = _get_attr("can_access")
_extract_token = _get_attr("_extract_token")  # type: ignore

__all__ = [
    "ROLE_ACCESS_MATRIX",
    "PERMISSION_ROLE_MATRIX",
    "resolve_user_from_request",
    "require_role",
    "admin_required",
    "has_role",
    "can_access",
    "_extract_token",
]
