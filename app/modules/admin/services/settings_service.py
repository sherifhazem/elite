"""Admin settings helpers backed by the centralized choices registry.

This module intentionally mutates the in-memory registry lists declared in
``app.core.choices.registry`` so that admin edits are reflected immediately across
forms, services, and monitoring endpoints without touching the database.
"""

from __future__ import annotations

from typing import Dict, Iterable, List

from app.logging.logger import get_logger
from app.core.choices.registry import CITIES, INDUSTRIES

_LOGGER = get_logger(__name__)
_REGISTRY_MAP = {"cities": CITIES, "industries": INDUSTRIES}


def _action_name(list_type: str, operation: str) -> str:
    """Return a standardized action label for logging."""

    normalized_type = (list_type or "").strip().lower()
    entity = "city" if normalized_type == "cities" else "industry"
    return f"{operation}_{entity}"


def _get_registry(list_type: str) -> List[str]:
    """Return the mutable registry list for the requested type."""

    normalized = (list_type or "").strip().lower()
    if normalized not in _REGISTRY_MAP:
        raise ValueError("قسم القائمة غير معروف.")
    return _REGISTRY_MAP[normalized]


def _normalize_value(value: str) -> str:
    """Strip whitespace and coerce to a usable string."""

    return (value or "").strip()


def _log(action: str, status: str, value: str, *, reason: str | None = None, items: Iterable[str] | None = None) -> None:
    """Emit structured diagnostics for all admin setting changes."""

    payload = {
        "admin_settings_action": action,
        "status": status,
        "value": value,
    }
    if reason:
        payload["reason"] = reason
    if items is not None:
        payload["items"] = list(items)

    if status == "success":
        _LOGGER.info("Admin settings change applied", extra={"log_payload": payload})
    else:
        _LOGGER.warning("Admin settings change rejected", extra={"log_payload": payload})


def get_all_settings() -> Dict[str, List[str]]:
    """Return a copy of all managed settings."""

    return {"cities": list(CITIES), "industries": list(INDUSTRIES)}


def get_list(list_type: str) -> List[str]:
    """Return a copy of the requested registry list."""

    return list(_get_registry(list_type))


def update_settings(list_type: str, new_values: Iterable[str]) -> List[str]:
    """Replace the entire list while enforcing uniqueness and non-empty values."""

    registry = _get_registry(list_type)
    seen = set()
    sanitized: List[str] = []
    for raw in new_values:
        value = _normalize_value(str(raw))
        if not value or value in seen:
            continue
        sanitized.append(value)
        seen.add(value)

    registry.clear()
    registry.extend(sanitized)
    _log(_action_name(list_type, "update"), "success", ",".join(sanitized), items=registry, reason="list_replaced")
    return list(registry)


def add_item(list_type: str, name: str) -> List[str]:
    """Append a new value to the registry list when valid."""

    registry = _get_registry(list_type)
    value = _normalize_value(name)
    action = _action_name(list_type, "add")

    if not value:
        _log(action, "error", value, reason="empty_value")
        raise ValueError("الاسم مطلوب.")
    if value in registry:
        _log(action, "error", value, reason="duplicate_value")
        raise ValueError("العنصر موجود بالفعل.")

    registry.append(value)
    _log(action, "success", value, items=registry, reason="added")
    return list(registry)


def delete_item(list_type: str, name: str) -> List[str]:
    """Remove a value from the registry list when present."""

    registry = _get_registry(list_type)
    value = _normalize_value(name)
    action = _action_name(list_type, "delete")

    if not value:
        _log(action, "error", value, reason="empty_value")
        raise ValueError("قيمة غير صالحة للحذف.")
    if value not in registry:
        _log(action, "error", value, reason="not_found")
        raise ValueError("لم يتم العثور على العنصر المطلوب.")

    registry.remove(value)
    _log(action, "success", value, items=registry, reason="deleted")
    return list(registry)


def update_item(list_type: str, old_name: str, new_name: str) -> List[str]:
    """Rename an existing entry while preventing duplicates."""

    registry = _get_registry(list_type)
    new_value = _normalize_value(new_name)
    old_value = _normalize_value(old_name)
    action = _action_name(list_type, "update")

    if not new_value:
        _log(action, "error", new_value, reason="empty_value")
        raise ValueError("الاسم مطلوب.")
    if old_value not in registry:
        _log(action, "error", old_value, reason="not_found")
        raise ValueError("لم يتم العثور على العنصر المطلوب.")
    if new_value != old_value and new_value in registry:
        _log(action, "error", new_value, reason="duplicate_value")
        raise ValueError("العنصر موجود بالفعل.")

    index = registry.index(old_value)
    registry[index] = new_value
    _log(action, "success", new_value, items=registry, reason="renamed")
    return list(registry)


__all__ = [
    "get_all_settings",
    "get_list",
    "update_settings",
    "add_item",
    "delete_item",
    "update_item",
]
