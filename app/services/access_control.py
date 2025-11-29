"""Shared access-control utilities reusable across all modules."""

from app.modules.members.services import roles as member_roles

ROLE_ACCESS_MATRIX = member_roles.ROLE_ACCESS_MATRIX
PERMISSION_ROLE_MATRIX = member_roles.PERMISSION_ROLE_MATRIX
resolve_user_from_request = member_roles.resolve_user_from_request
require_role = member_roles.require_role
admin_required = member_roles.admin_required
has_role = member_roles.has_role
can_access = member_roles.can_access
_extract_token = member_roles._extract_token  # type: ignore

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
