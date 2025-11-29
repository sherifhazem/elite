# LINKED: Added “Role Permissions” page under Site Settings for Superadmin.
# Allows managing and viewing system roles stored dynamically in Redis.
"""Utility helpers for managing role permissions stored in Redis."""

from __future__ import annotations

import json
from typing import Dict, List

from app import redis_client

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
