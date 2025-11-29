# LINKED: Implemented centralized Site Settings service using Redis for dropdown and general admin configurations.
"""Centralized service helpers for managing site settings stored in Redis."""

from __future__ import annotations

import copy
import json
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence

from app import redis_client

_REDIS_KEY = "elite:site:settings"
_ALLOWED_SECTIONS = {"cities", "industries", "general"}
_DEFAULT_SETTINGS: Dict[str, object] = {
    "cities": ["الرياض", "جدة", "الدمام"],
    "industries": ["مطاعم", "تجارة إلكترونية", "تعليم"],
    "general": {
        "support_email": "support@elite.sa",
        "support_phone": "+966500000000",
        "allow_company_auto_approval": False,
    },
}


def _ensure_defaults() -> None:
    """Seed Redis with default settings if the key does not exist."""

    if not redis_client.exists(_REDIS_KEY):
        redis_client.set(
            _REDIS_KEY,
            json.dumps(_DEFAULT_SETTINGS, ensure_ascii=False),
        )


def _load_settings() -> Dict[str, object]:
    """Return the raw settings payload from Redis ensuring defaults exist."""

    _ensure_defaults()
    raw_payload = redis_client.get(_REDIS_KEY)
    if not raw_payload:
        return copy.deepcopy(_DEFAULT_SETTINGS)
    data = json.loads(raw_payload)
    if not isinstance(data, dict):
        return copy.deepcopy(_DEFAULT_SETTINGS)
    # Merge with defaults to guarantee required sections exist.
    merged: Dict[str, object] = copy.deepcopy(_DEFAULT_SETTINGS)
    for section, value in data.items():
        if section in _ALLOWED_SECTIONS:
            merged[section] = value
    return merged


def _save_settings(payload: Mapping[str, object]) -> None:
    """Persist the provided settings payload to Redis."""

    redis_client.set(
        _REDIS_KEY,
        json.dumps(payload, ensure_ascii=False),
    )


def _sanitize_list_payload(values: Iterable[object]) -> List[str]:
    """Return a cleaned list of unique strings preserving order."""

    sanitized: List[str] = []
    seen = set()
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        sanitized.append(text)
        seen.add(text)
    return sanitized


def _coerce_iterable(value: object) -> Iterable[object]:
    """Convert supported payloads into an iterable of values."""

    if isinstance(value, (list, tuple, set)):
        return value
    if isinstance(value, str):
        normalized = value.replace("\r", "\n")
        return [item for item in normalized.split("\n")]
    if isinstance(value, Sequence):
        return list(value)
    raise ValueError("صيغة البيانات غير مدعومة لهذه القائمة.")


def _coerce_general_mapping(value: object) -> MutableMapping[str, object]:
    """Return a mutable mapping for the general settings payload."""

    if isinstance(value, MutableMapping):
        return value
    if isinstance(value, Mapping):
        return dict(value)
    raise ValueError("صيغة الإعدادات العامة غير صالحة.")


def get_all_settings() -> Dict[str, object]:
    """Return a deep copy of every site setting section."""

    return copy.deepcopy(_load_settings())


def get_section(section: str) -> object:
    """Return a single section from the site settings payload."""

    if section not in _ALLOWED_SECTIONS:
        raise ValueError("قسم الإعدادات غير معروف.")
    settings = _load_settings()
    return copy.deepcopy(settings[section])


def update_settings(section: str, new_data: object) -> object:
    """Update the provided section and persist the changes to Redis."""

    if section not in _ALLOWED_SECTIONS:
        raise ValueError("قسم الإعدادات غير معروف.")

    settings = _load_settings()

    if section in {"cities", "industries"}:
        iterable = _coerce_iterable(new_data)
        sanitized_values = _sanitize_list_payload(iterable)
        settings[section] = sanitized_values
        _save_settings(settings)
        return sanitized_values

    general_payload = _coerce_general_mapping(new_data)
    support_email = str(general_payload.get("support_email", "")).strip()
    support_phone = str(general_payload.get("support_phone", "")).strip()
    allow_raw = general_payload.get("allow_company_auto_approval", False)

    allow_auto = _parse_bool(allow_raw)
    general_settings = {
        "support_email": support_email,
        "support_phone": support_phone,
        "allow_company_auto_approval": allow_auto,
    }
    settings[section] = general_settings
    _save_settings(settings)
    return general_settings


def _parse_bool(value: object) -> bool:
    """Interpret common truthy values used in HTML forms."""

    if isinstance(value, str):
        return value.lower() in {"1", "true", "on", "yes"}
    return bool(value)


# ---------------------------------------------------------------------------
# Compatibility helpers for existing dropdown APIs throughout the codebase.
# ---------------------------------------------------------------------------

def get_list(list_type: str) -> List[str]:
    """Return the dropdown list for the provided type."""

    result = get_section(list_type)
    if not isinstance(result, list):
        raise ValueError("تنسيق القائمة غير صالح.")
    return result


def save_list(list_type: str, data: Iterable[str]) -> List[str]:
    """Persist the provided data for the specified dropdown list."""

    return update_settings(list_type, list(data))


def add_item(list_type: str, name: str) -> None:
    """Append a new item to the dropdown list when it doesn't exist."""

    trimmed = (name or "").strip()
    if not trimmed:
        raise ValueError("الاسم مطلوب.")
    items = get_list(list_type)
    if trimmed in items:
        raise ValueError("العنصر موجود بالفعل.")
    items.append(trimmed)
    update_settings(list_type, items)


def delete_item(list_type: str, name: str) -> None:
    """Remove an item from the dropdown list."""

    items = get_list(list_type)
    if name not in items:
        raise ValueError("لم يتم العثور على العنصر المطلوب.")
    items.remove(name)
    update_settings(list_type, items)


def update_item(list_type: str, old_name: str, new_name: str) -> None:
    """Rename an entry inside a dropdown list."""

    trimmed = (new_name or "").strip()
    if not trimmed:
        raise ValueError("الاسم مطلوب.")
    items = get_list(list_type)
    try:
        index = items.index(old_name)
    except ValueError as exc:
        raise ValueError("لم يتم العثور على العنصر المطلوب.") from exc
    if trimmed != old_name and trimmed in items:
        raise ValueError("العنصر موجود بالفعل.")
    items[index] = trimmed
    update_settings(list_type, items)


__all__ = [
    "get_all_settings",
    "get_section",
    "update_settings",
    "get_list",
    "save_list",
    "add_item",
    "delete_item",
    "update_item",
]
