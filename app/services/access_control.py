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


_LAZY_EXPORTS = {
    "ROLE_ACCESS_MATRIX",
    "PERMISSION_ROLE_MATRIX",
    "resolve_user_from_request",
    "require_role",
    "admin_required",
    "has_role",
    "can_access",
    "_extract_token",
}


def __getattr__(name: str) -> Any:  # pragma: no cover - shim for legacy imports
    """Dynamically fetch access-control helpers to avoid circular imports."""

    if name in _LAZY_EXPORTS:
        return _get_attr(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = sorted(_LAZY_EXPORTS)
