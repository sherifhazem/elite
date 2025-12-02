"""Centralized validation pipeline for cleaned request data."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

from flask import request

from app.logging.context import build_logging_context
from core.choices import registry

_REQUIRED_FIELDS = {
    "email",
    "password",
    "company_name",
    "phone_number",
    "industry",
    "city",
    "social_url",
}

_TEXT_LIMITS: dict[str, int] = {"description": 2000, "message": 5000}


def _is_url_field(field: str) -> bool:
    return field.lower().endswith("_url")


def _validate_url(field: str, value: Any) -> Tuple[bool, str | None]:
    if value in (None, ""):
        return True, None

    def is_valid(candidate: str) -> bool:
        parsed = urlparse(candidate)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    if isinstance(value, list):
        invalid = [item for item in value if isinstance(item, str) and not is_valid(item)]
        return (len(invalid) == 0, None if len(invalid) == 0 else ", ".join(invalid))

    if isinstance(value, str):
        return (is_valid(value), value if not is_valid(value) else None)

    return True, None


def _validate_required(combined: Dict[str, Any]) -> List[str]:
    missing: List[str] = []
    for field in _REQUIRED_FIELDS:
        if field in combined and (combined.get(field) in (None, "", [])):
            missing.append(field)
    return missing


def _validate_choices(combined: Dict[str, Any]) -> List[dict[str, Any]]:
    failures: List[dict[str, Any]] = []
    allowed_cities = registry.get_cities()
    allowed_industries = registry.get_industries()
    if "city" in combined and combined.get("city") not in (None, ""):
        if combined.get("city") not in allowed_cities:
            failures.append(
                {
                    "field": "city",
                    "allowed_values": list(allowed_cities),
                    "received_value": combined.get("city"),
                    "reason": "invalid_choice",
                }
            )
    if "industry" in combined and combined.get("industry") not in (None, ""):
        if combined.get("industry") not in allowed_industries:
            failures.append(
                {
                    "field": "industry",
                    "allowed_values": list(allowed_industries),
                    "received_value": combined.get("industry"),
                    "reason": "invalid_choice",
                }
            )
    return failures


def _validate_lengths(combined: Dict[str, Any]) -> List[dict[str, Any]]:
    failures: List[dict[str, Any]] = []
    for field, limit in _TEXT_LIMITS.items():
        value = combined.get(field)
        if isinstance(value, str) and len(value) > limit:
            failures.append({"field": field, "limit": limit, "length": len(value), "reason": "too_long"})
    return failures


def validate(normalized_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate normalized data and return a diagnostics bundle."""

    combined = normalized_data.get("combined", {})
    ctx = build_logging_context()

    missing_fields = _validate_required(combined)
    choice_failures = _validate_choices(combined)
    url_failures: List[dict[str, Any]] = []
    length_failures = _validate_lengths(combined)

    url_checked = False
    for field, value in combined.items():
        if _is_url_field(field):
            is_valid, invalid_value = _validate_url(field, value)
            ctx.add_breadcrumb("validation:url_validated")
            url_checked = True
            if not is_valid:
                url_failures.append(
                    {
                        "field": field,
                        "value": invalid_value,
                        "reason": "invalid_url_format",
                    }
                )
    if not url_checked:
        ctx.add_breadcrumb("validation:url_validated")

    if choice_failures:
        ctx.add_breadcrumb("validation:choices_validated")
    else:
        ctx.add_breadcrumb("validation:choices_validated")

    errors: List[dict[str, Any]] = []
    if missing_fields:
        errors.append({"missing_fields": missing_fields})
    if url_failures:
        errors.append({"invalid_urls": url_failures})
    if choice_failures:
        errors.append({"invalid_choices": choice_failures})
    if length_failures:
        errors.append({"too_large": length_failures})

    diagnostics = {
        "is_valid": len(errors) == 0,
        "missing_fields": missing_fields,
        "invalid_urls": url_failures,
        "invalid_choices": choice_failures,
        "too_large": length_failures,
        "errors": errors,
        "source": request.path,
    }
    ctx.validation = diagnostics
    return diagnostics


__all__ = ["validate"]
