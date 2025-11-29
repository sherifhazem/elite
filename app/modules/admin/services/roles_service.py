# LINKED: Added “Role Permissions” page under Site Settings for Superadmin.
# Allows managing and viewing system roles stored dynamically in Redis.
"""Utility helpers for managing role permissions stored in Redis."""

from __future__ import annotations

import json
from typing import Dict, List

from app import redis_client
from core.observability.logger import (
    get_service_logger,
    log_service_error,
    log_service_start,
    log_service_step,
    log_service_success,
)

ROLES_KEY = "elite:settings:role_permissions"

DEFAULT_PERMISSIONS: Dict[str, List[str]] = {
    "member": ["view_offers", "redeem_offers"],
    "company": ["view_dashboard", "create_offer", "view_redemptions"],
    "admin": [
        "view_admin",
        "manage_users",
        "manage_companies",
        "view_reports",
    ],
    "superadmin": ["all_permissions"],
}


service_logger = get_service_logger(__name__)


def _log(
    function: str,
    event: str,
    message: str,
    details: Dict[str, object] | None = None,
    level: str = "INFO",
) -> None:
    """Emit standardized logs for role service operations."""

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


def get_all_roles() -> List[str]:
    """Return the list of known roles."""

    _log("get_all_roles", "service_start", "Fetching all available roles")
    roles = list(DEFAULT_PERMISSIONS.keys())
    _log("get_all_roles", "service_complete", "Roles list prepared", {"count": len(roles)})
    return roles


def get_role_permissions() -> Dict[str, List[str]]:
    """Return the configured role permissions, falling back to defaults."""

    _log("get_role_permissions", "service_start", "Reading role permissions from Redis")
    data = redis_client.get(ROLES_KEY)
    if data:
        try:
            payload = json.loads(data)
            if isinstance(payload, dict):
                _log(
                    "get_role_permissions",
                    "db_query",
                    "Role permissions loaded",
                    {"roles": list(payload.keys())},
                )
                return payload
        except json.JSONDecodeError:
            _log(
                "get_role_permissions",
                "soft_failure",
                "Invalid JSON detected in Redis role permissions",
                {"raw": data},
                level="WARNING",
            )
    redis_client.set(ROLES_KEY, json.dumps(DEFAULT_PERMISSIONS))
    _log(
        "get_role_permissions",
        "db_write_success",
        "Default role permissions restored to Redis",
        {"roles": list(DEFAULT_PERMISSIONS.keys())},
    )
    restored = json.loads(json.dumps(DEFAULT_PERMISSIONS))
    _log(
        "get_role_permissions",
        "service_complete",
        "Role permissions ready",
        {"roles": list(restored.keys())},
    )
    return restored


def save_role_permissions(new_data: Dict[str, List[str]]) -> None:
    """Persist the provided role-to-permissions mapping."""

    _log(
        "save_role_permissions",
        "service_start",
        "Persisting updated role permissions",
        {"roles": list(new_data.keys())},
    )
    redis_client.set(ROLES_KEY, json.dumps(new_data))
    _log(
        "save_role_permissions",
        "db_write_success",
        "Role permissions saved",
        {"roles": list(new_data.keys())},
    )


__all__ = [
    "ROLES_KEY",
    "DEFAULT_PERMISSIONS",
    "get_all_roles",
    "get_role_permissions",
    "save_role_permissions",
]
