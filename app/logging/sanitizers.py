"""Utilities for masking and normalizing sensitive payload fields."""

from __future__ import annotations

from typing import Any, Mapping

SENSITIVE_FIELDS = {
    "password",
    "token",
    "authorization",
    "cookie",
    "cookies",
    "csrf_token",
}
MASK = "***"


def _is_sensitive(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(field in normalized for field in SENSITIVE_FIELDS)


def mask_value(value: Any) -> Any:
    """Return a masked placeholder for sensitive values."""

    if value is None:
        return None
    return MASK


def sanitize_mapping(data: Mapping[str, Any]) -> dict[str, Any]:
    """Mask sensitive keys in a mapping recursively."""

    sanitized: dict[str, Any] = {}
    for key, value in data.items():
        if _is_sensitive(key):
            sanitized[key] = mask_value(value)
            continue
        sanitized[key] = sanitize_value(value)
    return sanitized


def sanitize_value(value: Any) -> Any:
    """Recursively sanitize dictionaries and lists."""

    if isinstance(value, Mapping):
        return sanitize_mapping(value)
    if isinstance(value, list):
        return [sanitize_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_value(item) for item in value)
    return value


def filter_headers(headers: Mapping[str, Any]) -> dict[str, Any]:
    """Return headers without sensitive entries."""

    return {k: v for k, v in headers.items() if not _is_sensitive(k)}


def sanitize_payload(data: Any) -> Any:
    """Sanitize arbitrary payload content."""

    return sanitize_value(data)


__all__ = [
    "filter_headers",
    "mask_value",
    "sanitize_mapping",
    "sanitize_payload",
]
