"""Request-scoped extraction and normalization utilities."""

from __future__ import annotations

from typing import Any, Dict, Tuple

from flask import Request

from app.logging.sanitizers import filter_headers, sanitize_payload
from app.core.normalization.url_normalizer import normalize_url


_URL_FIELDS = {"website_url", "social_url"}


def _should_normalize(field: str) -> bool:
    normalized_key = field.lower()
    return normalized_key in _URL_FIELDS or normalized_key.endswith("_url")


def _as_mapping(multidict: Any) -> dict[str, Any]:
    try:
        return {key: value if len(value) > 1 else value[0] for key, value in multidict.lists()}
    except Exception:
        try:
            return {key: value for key, value in multidict.items()}
        except Exception:
            return {}


def _clean_scalar(field: str, value: Any) -> Any:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped == "":
            return None
        normalized = normalize_url(stripped) if _should_normalize(field) else stripped
        return normalized
    return value


def _clean_value(field: str, value: Any) -> Any:
    if isinstance(value, list):
        return [_clean_scalar(field, item) for item in value]
    return _clean_scalar(field, value)


def extract_raw_data(request: Request) -> Dict[str, Any]:
    """Return raw payload segments from the Flask request."""

    try:
        json_payload = request.get_json(silent=True)
    except Exception:
        json_payload = None

    form_payload = _as_mapping(request.form) if request.form else {}
    query_payload = _as_mapping(request.args) if request.args else {}

    headers = filter_headers(dict(request.headers))

    combined: dict[str, Any] = {}
    combined.update(query_payload)
    combined.update(form_payload)
    if isinstance(json_payload, dict):
        combined.update(json_payload)

    raw = {
        "json": json_payload if isinstance(json_payload, dict) else None,
        "form": form_payload,
        "query": query_payload,
        "headers": headers,
        "combined": combined,
    }
    return raw


def normalize_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize string values, *_url fields, and collapse empties."""

    normalization_events: list[dict[str, Any]] = []

    def normalize_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        for key, value in mapping.items():
            normalized_value = _clean_value(key, value)
            if _should_normalize(key):
                if isinstance(value, list):
                    pairs = [pair for pair in zip(value, normalized_value) if pair[0] != pair[1]]  # type: ignore[arg-type]
                    for before, after in pairs:
                        normalization_events.append({"field": key, "from": before, "to": after})
                elif value != normalized_value:
                    normalization_events.append({"field": key, "from": value, "to": normalized_value})
            normalized[key] = normalized_value
        return normalized

    normalized_json = normalize_mapping(raw_data.get("json") or {})
    normalized_form = normalize_mapping(raw_data.get("form") or {})
    normalized_query = normalize_mapping(raw_data.get("query") or {})

    combined: dict[str, Any] = {}
    combined.update(normalized_query)
    combined.update(normalized_form)
    combined.update(normalized_json)

    return {
        "json": normalized_json,
        "form": normalized_form,
        "query": normalized_query,
        "combined": combined,
        "normalization": normalization_events,
    }


def validate_choices(normalized_data: Dict[str, Any]) -> Tuple[bool, list[dict[str, Any]]]:
    """Validate registry-backed choice fields."""

    from app.core.choices import registry

    combined = normalized_data.get("combined", {})
    errors: list[dict[str, Any]] = []

    allowed_cities = registry.get_cities()
    city = combined.get("city")
    if city is not None and city not in allowed_cities:
        errors.append(
            {
                "field": "city",
                "allowed_values": list(allowed_cities),
                "received_value": city,
                "reason": "invalid_choice",
            }
        )

    allowed_industries = registry.get_industries()
    industry = combined.get("industry")
    if industry is not None and industry not in allowed_industries:
        errors.append(
            {
                "field": "industry",
                "allowed_values": list(allowed_industries),
                "received_value": industry,
                "reason": "invalid_choice",
            }
        )

    return len(errors) == 0, errors


def build_cleaned_payload(raw_data: Dict[str, Any], normalized_data: Dict[str, Any]) -> Dict[str, Any]:
    """Combine original and normalized payloads into a canonical cleaned mapping."""

    cleaned = dict(normalized_data.get("combined", {}))
    cleaned["__original"] = sanitize_payload(raw_data)
    cleaned["__normalized"] = sanitize_payload(normalized_data)
    cleaned["__diagnostics"] = {
        "normalization": normalized_data.get("normalization", []),
        "sources": [key for key in ("json", "form", "query") if raw_data.get(key)],
    }
    return cleaned


__all__ = [
    "extract_raw_data",
    "normalize_data",
    "validate_choices",
    "build_cleaned_payload",
]
