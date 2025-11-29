# LINKED: Added “Role Permissions” page under Site Settings for Superadmin.
# Allows managing and viewing system roles stored dynamically in Redis.
"""Utility helpers for managing role permissions stored in Redis."""

from __future__ import annotations

import json
from typing import Dict, List

from app import redis_client
<<<<<<< HEAD
from core.observability.logger import (
    get_service_logger,
    log_service_error,
    log_service_start,
    log_service_step,
    log_service_success,
)
=======
>>>>>>> parent of 29a5adb (Add local observability layer and structured logging (#168))

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


<<<<<<< HEAD
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


=======
>>>>>>> parent of 29a5adb (Add local observability layer and structured logging (#168))
def get_all_roles() -> List[str]:
    """Return the list of known roles."""

    return list(DEFAULT_PERMISSIONS.keys())


def get_role_permissions() -> Dict[str, List[str]]:
    """Return the configured role permissions, falling back to defaults."""

    data = redis_client.get(ROLES_KEY)
    if data:
        try:
            payload = json.loads(data)
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            pass
    redis_client.set(ROLES_KEY, json.dumps(DEFAULT_PERMISSIONS))
    return json.loads(json.dumps(DEFAULT_PERMISSIONS))


def save_role_permissions(new_data: Dict[str, List[str]]) -> None:
    """Persist the provided role-to-permissions mapping."""

    redis_client.set(ROLES_KEY, json.dumps(new_data))


__all__ = [
    "ROLES_KEY",
    "DEFAULT_PERMISSIONS",
    "get_all_roles",
    "get_role_permissions",
    "save_role_permissions",
]
