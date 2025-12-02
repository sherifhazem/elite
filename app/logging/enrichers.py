"""Helpers to enrich log payloads with request and response data."""

from __future__ import annotations

from functools import wraps
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Dict, TypeVar

from flask import Response, request

from .context import build_logging_context
from .sanitizers import filter_headers, sanitize_payload

F = TypeVar("F", bound=Callable[..., Any])


def _normalize_dict(multidict: Any) -> dict[str, Any]:
    try:
        return {key: value if len(value) > 1 else value[0] for key, value in multidict.lists()}
    except Exception:
        try:
            return {key: value for key, value in multidict.items()}
        except Exception:
            return {}


def capture_incoming_request() -> dict[str, Any]:
    """Capture the inbound HTTP request components."""

    json_payload = None
    try:
        json_payload = request.get_json(silent=True)
    except Exception:
        json_payload = None

    form_data = _normalize_dict(request.form) if request.form else {}
    query_params = _normalize_dict(request.args) if request.args else {}

    files = {}
    for field, storage in request.files.items():
        filename = getattr(storage, "filename", None)
        extension = Path(filename).suffix if filename else None
        files[field] = {"filename": filename, "extension": extension}

    headers = filter_headers(dict(request.headers))

    payload = {
        "method": request.method,
        "path": request.full_path.rstrip("?") or request.path,
        "query_params": sanitize_payload(query_params),
        "form_data": sanitize_payload(form_data),
        "json": sanitize_payload(json_payload) if json_payload is not None else None,
        "headers": headers,
        "files": files,
    }
    return payload


def capture_outgoing_response(response: Response) -> dict[str, Any]:
    """Capture response details for logging."""

    json_body = None
    try:
        json_body = response.get_json(silent=True)
    except Exception:
        json_body = None

    error_payload = None
    if response.status_code >= 400:
        if json_body is not None:
            error_payload = json_body
        else:
            try:
                error_payload = response.get_data(as_text=True)
            except Exception:
                error_payload = None

    redirect_target = response.headers.get("Location")
    raw_bytes = response.get_data() or b""
    response_size = len(raw_bytes)

    payload = {
        "status_code": response.status_code,
        "json": sanitize_payload(json_body) if json_body is not None else None,
        "error": sanitize_payload(error_payload) if error_payload is not None else None,
        "redirect": redirect_target,
        "response_size": response_size,
    }
    return payload


def extract_validation_state(response: Response, incoming_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Derive validation diagnostics for client errors."""

    status = getattr(response, "status_code", 200)
    if status not in (400, 422):
        return {}

    body = None
    try:
        body = response.get_json(silent=True)
    except Exception:
        body = None

    missing_fields = []
    invalid_fields: dict[str, Any] = {}
    allowed_values: dict[str, Any] = {}
    diagnostic_message = "Validation failed"

    if isinstance(body, dict):
        missing_fields = body.get("missing_fields") or body.get("required") or []
        invalid_fields = body.get("invalid_fields") or body.get("errors") or {}
        allowed_values = body.get("allowed_values") or body.get("choices") or {}
        diagnostic_message = body.get("message") or body.get("detail") or diagnostic_message

    received_values = incoming_payload.get("json") or incoming_payload.get("form_data") or incoming_payload.get("query_params") or {}

    snapshot = {
        "event": "validation_failed",
        "missing_fields": missing_fields,
        "invalid_fields": invalid_fields,
        "allowed_values": allowed_values,
        "received_values": sanitize_payload(received_values),
        "diagnostic": diagnostic_message,
    }
    return snapshot


def serialize_exception(exc: Exception) -> dict[str, Any]:
    """Render a structured exception payload."""

    import traceback

    exc_type = type(exc).__name__
    message = str(exc)
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    frame_summary = traceback.extract_tb(exc.__traceback__)[-1] if exc.__traceback__ else None

    location = {
        "file": frame_summary.filename if frame_summary else None,
        "function": frame_summary.name if frame_summary else None,
        "line": frame_summary.lineno if frame_summary else None,
    }

    return {
        "exception_type": exc_type,
        "exception_message": message,
        "traceback": tb,
        **location,
    }


def snapshot_payload() -> dict[str, Any]:
    """Capture a sanitized snapshot of the incoming payload for error reporting."""

    try:
        body = request.get_json(silent=True)
    except Exception:
        body = None

    snapshot = {
        "path": request.path,
        "method": request.method,
        "query": sanitize_payload(_normalize_dict(request.args) if request.args else {}),
        "form": sanitize_payload(_normalize_dict(request.form) if request.form else {}),
        "json": sanitize_payload(body) if body is not None else None,
    }
    return snapshot


def trace_execution(message: str | None = None) -> Callable[[F], F]:
    """Decorator to automatically add breadcrumbs and timing around service calls."""

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):  # type: ignore[misc]
            ctx = build_logging_context()
            ctx.add_breadcrumb(
                message or func.__name__,
                file=getattr(func, "__code__", None).co_filename if hasattr(func, "__code__") else None,
                function=getattr(func, "__name__", None),
                line=getattr(func, "__code__", None).co_firstlineno if hasattr(func, "__code__") else None,
            )
            started = perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                ctx.mark_service_time((perf_counter() - started) * 1000)

        return wrapper  # type: ignore[return-value]

    return decorator


__all__ = [
    "capture_incoming_request",
    "capture_outgoing_response",
    "extract_validation_state",
    "serialize_exception",
    "snapshot_payload",
    "trace_execution",
]
