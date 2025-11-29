# LINKED: Implemented centralized Site Settings service using Redis for dropdown and general admin configurations.
"""Centralized service helpers for managing site settings stored in Redis."""

from __future__ import annotations

import copy
import json
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence

from app import redis_client
from core.observability.logger import (
    get_service_logger,
    log_service_error,
    log_service_start,
    log_service_step,
    log_service_success,
)

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


service_logger = get_service_logger(__name__)


def _log(
    function: str,
    event: str,
    message: str,
    details: Dict[str, object] | None = None,
    level: str = "INFO",
) -> None:
    """Emit standardized observability events for settings operations."""

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


def _ensure_defaults() -> None:
    """Seed Redis with default settings if the key does not exist."""

    if not redis_client.exists(_REDIS_KEY):
        redis_client.set(
            _REDIS_KEY,
            json.dumps(_DEFAULT_SETTINGS, ensure_ascii=False),
        )
        _log(
            "_ensure_defaults",
            "db_write_success",
            "Default settings seeded in Redis",
            {"sections": list(_DEFAULT_SETTINGS.keys())},
        )


def _load_settings() -> Dict[str, object]:
    """Return the raw settings payload from Redis ensuring defaults exist."""

    _ensure_defaults()
    _log("_load_settings", "db_query", "Loading settings from Redis")
    raw_payload = redis_client.get(_REDIS_KEY)
    if not raw_payload:
        _log(
            "_load_settings",
            "soft_failure",
            "Settings missing in Redis, using defaults",
            level="WARNING",
        )
        return copy.deepcopy(_DEFAULT_SETTINGS)
    data = json.loads(raw_payload)
    if not isinstance(data, dict):
        _log(
            "_load_settings",
            "soft_failure",
            "Malformed settings payload detected",
            {"type": str(type(data))},
            level="WARNING",
        )
        return copy.deepcopy(_DEFAULT_SETTINGS)
    # Merge with defaults to guarantee required sections exist.
    merged: Dict[str, object] = copy.deepcopy(_DEFAULT_SETTINGS)
    for section, value in data.items():
        if section in _ALLOWED_SECTIONS:
            merged[section] = value
    _log("_load_settings", "service_checkpoint", "Settings payload normalized", {"sections": list(merged.keys())})
    return merged


def _save_settings(payload: Mapping[str, object]) -> None:
    """Persist the provided settings payload to Redis."""

    redis_client.set(
        _REDIS_KEY,
        json.dumps(payload, ensure_ascii=False),
    )
    _log("_save_settings", "db_write_success", "Settings persisted", {"sections": list(payload.keys())})


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

    _log("get_all_settings", "service_start", "Retrieving all settings")
    payload = copy.deepcopy(_load_settings())
    _log("get_all_settings", "service_complete", "All settings returned", {"sections": list(payload.keys())})
    return payload


def get_section(section: str) -> object:
    """Return a single section from the site settings payload."""

    if section not in _ALLOWED_SECTIONS:
        _log(
            "get_section",
            "validation_failure",
            "Unknown settings section requested",
            {"section": section},
            level="ERROR",
        )
        raise ValueError("قسم الإعدادات غير معروف.")
    _log("get_section", "validation_success", "Section validated", {"section": section})
    settings = _load_settings()
    payload = copy.deepcopy(settings[section])
    _log("get_section", "service_complete", "Section returned", {"section": section})
    return payload


def update_settings(section: str, new_data: object) -> object:
    """Update the provided section and persist the changes to Redis."""

    if section not in _ALLOWED_SECTIONS:
        _log(
            "update_settings",
            "validation_failure",
            "Attempted to update unknown section",
            {"section": section},
            level="ERROR",
        )
        raise ValueError("قسم الإعدادات غير معروف.")

    _log("update_settings", "service_start", "Updating settings section", {"section": section})
    settings = _load_settings()

    if section in {"cities", "industries"}:
        iterable = _coerce_iterable(new_data)
        sanitized_values = _sanitize_list_payload(iterable)
        settings[section] = sanitized_values
        _save_settings(settings)
        _log(
            "update_settings",
            "db_write_success",
            "List settings updated",
            {"section": section, "items": len(sanitized_values)},
        )
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
    _log(
        "update_settings",
        "db_write_success",
        "General settings updated",
        {"section": section, "allow_auto": allow_auto},
    )
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
        _log(
            "get_list",
            "validation_failure",
            "Expected list section but received other type",
            {"section": list_type},
            level="ERROR",
        )
        raise ValueError("تنسيق القائمة غير صالح.")
    _log("get_list", "validation_success", "List section retrieved", {"section": list_type})
    return result


def save_list(list_type: str, data: Iterable[str]) -> List[str]:
    """Persist the provided data for the specified dropdown list."""

    return update_settings(list_type, list(data))


def add_item(list_type: str, name: str) -> None:
    """Append a new item to the dropdown list when it doesn't exist."""

    trimmed = (name or "").strip()
    if not trimmed:
        _log("add_item", "validation_failure", "Attempted to add empty list item", {"section": list_type}, level="ERROR")
        raise ValueError("الاسم مطلوب.")
    items = get_list(list_type)
    if trimmed in items:
        _log(
            "add_item",
            "soft_failure",
            "List item already exists",
            {"section": list_type, "item": trimmed},
            level="WARNING",
        )
        raise ValueError("العنصر موجود بالفعل.")
    items.append(trimmed)
    update_settings(list_type, items)


def delete_item(list_type: str, name: str) -> None:
    """Remove an item from the dropdown list."""

    items = get_list(list_type)
    if name not in items:
        _log(
            "delete_item",
            "soft_failure",
            "Attempted to delete missing item",
            {"section": list_type, "item": name},
            level="WARNING",
        )
        raise ValueError("لم يتم العثور على العنصر المطلوب.")
    items.remove(name)
    update_settings(list_type, items)


def update_item(list_type: str, old_name: str, new_name: str) -> None:
    """Rename an entry inside a dropdown list."""

    trimmed = (new_name or "").strip()
    if not trimmed:
        _log(
            "update_item",
            "validation_failure",
            "Attempted to rename item to empty value",
            {"section": list_type},
            level="ERROR",
        )
        raise ValueError("الاسم مطلوب.")
    items = get_list(list_type)
    try:
        index = items.index(old_name)
    except ValueError as exc:
        _log(
            "update_item",
            "soft_failure",
            "Original item not found",
            {"section": list_type, "item": old_name},
            level="WARNING",
        )
        raise ValueError("لم يتم العثور على العنصر المطلوب.") from exc
    if trimmed != old_name and trimmed in items:
        _log(
            "update_item",
            "soft_failure",
            "Duplicate item detected during rename",
            {"section": list_type, "item": trimmed},
            level="WARNING",
        )
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
