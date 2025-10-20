# LINKED: Added comprehensive Site Settings section in Admin Panel.
# Includes Cities & Industries dynamic management integrated with Redis backend.
# LINKED: Upgraded settings storage to Redis backend for dynamic dropdown lists.
# Replaced local JSON persistence with Redis keys (elite:settings:cities, elite:settings:industries).
"""Utility helpers for managing admin-configurable dropdown lists via Redis."""

from __future__ import annotations

import json
from typing import Dict, Iterable, List

from app import redis_client

_ALLOWED_LISTS = {"cities", "industries"}
_KEY_TEMPLATE = "elite:settings:{list_type}"
_DEFAULT_VALUES: Dict[str, List[str]] = {
    "cities": ["الرياض", "جدة", "الدمام"],
    "industries": ["مطاعم", "تجارة إلكترونية", "تعليم"],
}


def _redis_key(list_type: str) -> str:
    """Return the Redis key for the provided list type."""

    if list_type not in _ALLOWED_LISTS:
        raise ValueError(f"Unsupported list type: {list_type}")
    return _KEY_TEMPLATE.format(list_type=list_type)


def _ensure_defaults() -> None:
    """Seed Redis with default values when keys are missing."""

    for list_type, default_values in _DEFAULT_VALUES.items():
        key = _redis_key(list_type)
        if not redis_client.exists(key):
            redis_client.set(key, json.dumps(default_values, ensure_ascii=False))


def get_list(list_type: str) -> List[str]:
    """Fetch list (cities or industries) from Redis."""

    _ensure_defaults()
    key = _redis_key(list_type)
    data = redis_client.get(key)
    return json.loads(data) if data else []


def save_list(list_type: str, data: Iterable[str]) -> None:
    """Persist the provided iterable to Redis as a JSON list."""

    key = _redis_key(list_type)
    payload = list(data)
    redis_client.set(key, json.dumps(payload, ensure_ascii=False), ex=None)


def add_item(list_type: str, name: str) -> None:
    """Add new item to the specified list if it doesn't already exist."""

    trimmed = (name or "").strip()
    if not trimmed:
        raise ValueError("الاسم مطلوب.")

    data = get_list(list_type)
    if trimmed not in data:
        data.append(trimmed)
        save_list(list_type, data)
    else:
        raise ValueError("العنصر موجود بالفعل.")


def delete_item(list_type: str, name: str) -> None:
    """Remove item from list."""

    data = get_list(list_type)
    if name in data:
        data.remove(name)
        save_list(list_type, data)
    else:
        raise ValueError("لم يتم العثور على العنصر المطلوب.")


def update_item(list_type: str, old_name: str, new_name: str) -> None:
    """Rename item in list."""

    trimmed = (new_name or "").strip()
    if not trimmed:
        raise ValueError("الاسم مطلوب.")

    data = get_list(list_type)
    try:
        idx = data.index(old_name)
    except ValueError as exc:
        raise ValueError("لم يتم العثور على العنصر المطلوب.") from exc

    if trimmed != old_name and trimmed in data:
        raise ValueError("العنصر موجود بالفعل.")

    data[idx] = trimmed
    save_list(list_type, data)


# Ensure Redis defaults are populated on import so dropdowns work immediately.
_ensure_defaults()


__all__ = [
    "get_list",
    "save_list",
    "add_item",
    "delete_item",
    "update_item",
]
