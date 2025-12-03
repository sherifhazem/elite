"""Authoritative registry for user-facing choices (cities and industries)."""

from __future__ import annotations

from typing import Iterable, List, Tuple

# NOTE: These defaults are the source of truth for seed values.
CITIES: List[str] = ["الرياض", "جدة", "الدمام"]
INDUSTRIES: List[str] = ["مطاعم", "تجارة إلكترونية", "تعليم"]


def _load_managed_list(list_type: str, fallback: Iterable[str]) -> List[str]:
    """Return the managed list from settings, falling back to registry defaults."""

    try:
        from app.services.settings_service import get_list

        values = get_list(list_type, active_only=True)
        if isinstance(values, list) and values:
            return [value for value in values if value]
    except Exception:
        # Settings may be unavailable during boot or tests; fall back gracefully.
        pass
    return list(fallback)


def get_cities() -> List[str]:
    """Fetch the authoritative cities list."""

    return _load_managed_list("cities", CITIES)


def get_industries() -> List[str]:
    """Fetch the authoritative industries list."""

    return _load_managed_list("industries", INDUSTRIES)


def validate_choice(value: str, allowed: Iterable[str], field_name: str) -> Tuple[bool, str]:
    """Validate that a value exists in the allowed list with diagnostics."""

    allowed_values = [item for item in allowed if item]
    received_value = (value or "").strip()
    is_valid = received_value in allowed_values
    diagnostic = ""

    if not is_valid:
        diagnostic = f"{field_name} must be one of the allowed options."

    try:
        from app.logging.context import build_logging_context

        ctx = build_logging_context()
        ctx.add_breadcrumb(f"validation:{field_name}_checked")
        ctx.validation.setdefault("choices", []).append(
            {
                "field": field_name,
                "allowed_values": allowed_values,
                "received_value": received_value,
                "reason": None if is_valid else "value_not_in_list",
                "result": "valid" if is_valid else "invalid",
            }
        )
    except Exception:
        # Logging context may not be available early in app startup or CLI use.
        pass

    return is_valid, diagnostic


__all__ = [
    "CITIES",
    "INDUSTRIES",
    "get_cities",
    "get_industries",
    "validate_choice",
]
