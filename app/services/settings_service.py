# LINKED: Added admin-managed dropdown system for Cities and Industries.
# Introduced unified Settings Service and admin UI for dynamic list management.
"""Utility helpers for managing dynamic dropdown configuration lists."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Iterable, List
from uuid import uuid4

_SETTINGS_LOCK = RLock()
_CACHE: Dict[str, List[Dict[str, Any]]] | None = None

_SETTINGS_FILE = Path(__file__).resolve().parents[2] / "config" / "settings_data.json"

_DEFAULT_SETTINGS: Dict[str, List[Dict[str, Any]]] = {
    "cities": [
        {"id": "city-riyadh", "name": "الرياض", "active": True},
        {"id": "city-jeddah", "name": "جدة", "active": True},
        {"id": "city-dammam", "name": "الدمام", "active": True},
        {"id": "city-khobar", "name": "الخبر", "active": True},
    ],
    "industries": [
        {"id": "industry-restaurants", "name": "مطاعم", "active": True},
        {"id": "industry-medical", "name": "خدمات طبية", "active": True},
        {"id": "industry-education", "name": "تعليم", "active": True},
        {"id": "industry-ecommerce", "name": "تجارة إلكترونية", "active": True},
    ],
}

_VALID_TYPES = frozenset(_DEFAULT_SETTINGS.keys())


def _ensure_storage_file() -> None:
    """Make sure the JSON storage file exists with baseline data."""

    with _SETTINGS_LOCK:
        if not _SETTINGS_FILE.parent.exists():
            _SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not _SETTINGS_FILE.exists():
            _write_file(_DEFAULT_SETTINGS)


def _write_file(payload: Dict[str, List[Dict[str, Any]]]) -> None:
    """Persist the provided payload to disk atomically."""

    tmp_path = _SETTINGS_FILE.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    tmp_path.replace(_SETTINGS_FILE)


def _load_cache() -> None:
    """Load configuration lists into the in-memory cache."""

    global _CACHE
    if _CACHE is not None:
        return

    _ensure_storage_file()
    with _SETTINGS_FILE.open("r", encoding="utf-8") as fh:
        try:
            data: Dict[str, List[Dict[str, Any]]] = json.load(fh)
        except json.JSONDecodeError:
            data = deepcopy(_DEFAULT_SETTINGS)
            _write_file(data)
    for key in _VALID_TYPES:
        data.setdefault(key, deepcopy(_DEFAULT_SETTINGS[key]))
    _CACHE = data


def _assert_valid_type(list_type: str) -> None:
    """Raise ValueError if the provided list type is not supported."""

    if list_type not in _VALID_TYPES:
        raise ValueError(f"Unsupported list type: {list_type}")


def reload_cache() -> None:
    """Force reloading the cache from storage."""

    global _CACHE
    with _SETTINGS_LOCK:
        _CACHE = None
        _load_cache()


def _get_cache() -> Dict[str, List[Dict[str, Any]]]:
    """Return the in-memory cache, loading it if required."""

    _load_cache()
    return _CACHE or {}


def _normalize_name(name: str) -> str:
    """Normalize incoming names by trimming whitespace."""

    return " ".join(part for part in name.split() if part)


def get_entries(list_type: str) -> List[Dict[str, Any]]:
    """Return a copy of all entries for the requested list type."""

    _assert_valid_type(list_type)
    cache = _get_cache()
    return deepcopy(cache.get(list_type, []))


def get_list(list_type: str, *, include_inactive: bool = False) -> List[str]:
    """Return item names for the target list, optionally filtering inactive ones."""

    entries = get_entries(list_type)
    if include_inactive:
        return [entry["name"] for entry in entries]
    return [entry["name"] for entry in entries if entry.get("active", True)]


def save_to_storage(list_type: str, data: Iterable[Dict[str, Any]]) -> None:
    """Persist the provided data list for the specified type."""

    _assert_valid_type(list_type)
    with _SETTINGS_LOCK:
        cache = _get_cache()
        cache[list_type] = [deepcopy(item) for item in data]
        _write_file(cache)


def add_item(list_type: str, name: str, *, active: bool = True) -> Dict[str, Any]:
    """Add a new item to the requested list and persist it."""

    normalized = _normalize_name(name)
    if not normalized:
        raise ValueError("الاسم مطلوب.")

    with _SETTINGS_LOCK:
        _assert_valid_type(list_type)
        cache = _get_cache()
        entries = cache.setdefault(list_type, [])
        if any(entry["name"].strip().lower() == normalized.lower() for entry in entries):
            raise ValueError("العنصر موجود بالفعل.")
        item = {"id": uuid4().hex, "name": normalized, "active": bool(active)}
        entries.append(item)
        _write_file(cache)
        return deepcopy(item)


def update_item(list_type: str, item_id: str, *, name: str | None = None, active: bool | None = None) -> Dict[str, Any]:
    """Update an existing item identified by its ID."""

    _assert_valid_type(list_type)
    with _SETTINGS_LOCK:
        cache = _get_cache()
        entries = cache.get(list_type, [])
        for entry in entries:
            if entry.get("id") == item_id:
                new_name = _normalize_name(name or entry["name"])
                if not new_name:
                    raise ValueError("الاسم مطلوب.")
                if any(
                    other.get("id") != item_id
                    and other.get("name", "").strip().lower() == new_name.lower()
                    for other in entries
                ):
                    raise ValueError("العنصر موجود بالفعل.")
                entry["name"] = new_name
                if active is not None:
                    entry["active"] = bool(active)
                _write_file(cache)
                return deepcopy(entry)
        raise ValueError("لم يتم العثور على العنصر المطلوب.")


def delete_item(list_type: str, item_id: str) -> None:
    """Remove an item from the specified list by ID."""

    _assert_valid_type(list_type)
    with _SETTINGS_LOCK:
        cache = _get_cache()
        entries = cache.get(list_type, [])
        new_entries = [entry for entry in entries if entry.get("id") != item_id]
        if len(new_entries) == len(entries):
            raise ValueError("لم يتم العثور على العنصر المطلوب.")
        cache[list_type] = new_entries
        _write_file(cache)
