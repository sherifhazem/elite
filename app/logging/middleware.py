"""Global middleware wiring for structured request logging."""

from __future__ import annotations

import logging
from http import HTTPStatus
from time import perf_counter
from uuid import uuid4

from flask import Flask, Response, g, jsonify, request
from werkzeug.exceptions import HTTPException

from .context import build_logging_context
from .enrichers import (
    capture_outgoing_response,
    extract_validation_state,
    serialize_exception,
    snapshot_payload,
)
from .logger import get_logger
from app.core.cleaning.request_cleaner import extract_raw_data
from app.core.validation.validator import validate

logger = get_logger()


def _merge_validation(existing: dict[str, object], extracted: dict[str, object]) -> dict[str, object]:
    merged: dict[str, object] = {**existing}

    for key, value in extracted.items():
        if key in {"failures", "choices"} and isinstance(value, list):
            merged[key] = list(existing.get(key, [])) + list(value)
            continue
        if key not in merged:
            merged[key] = value
            continue
        merged[key] = merged.get(key) or value

    return merged


def _set_response_ids(response: Response, *, request_id: str, trace_id: str, parent_id: str | None) -> None:
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Trace-ID"] = trace_id
    if parent_id:
        response.headers["X-Parent-ID"] = parent_id


def register_logging_middleware(app: Flask) -> None:
    """Attach the centralized logging middleware to the Flask app."""

    if getattr(app, "_structured_logging_installed", False):
        return
    app._structured_logging_installed = True

    @app.before_request
    def _start_observation() -> None:
        from app.core.cleaning.request_cleaner import normalize_data, build_cleaned_payload
        
        ctx = build_logging_context()
        g.request_id = ctx.request_id
        g.trace_id = ctx.trace_id
        g.parent_id = ctx.parent_id
        middleware_t0 = perf_counter()

        raw_payload = extract_raw_data(request)
        normalized_payload = normalize_data(raw_payload)
        cleaned_payload = build_cleaned_payload(raw_payload, normalized_payload)
        
        request.incoming_payload = raw_payload
        request.normalized_payload = normalized_payload
        request.cleaned = cleaned_payload
        
        ctx.incoming_payload.update(raw_payload)

        validation_info = validate(cleaned_payload) # Use cleaned payload for validation
        request.validation_info = validation_info
        if validation_info:
            ctx.validation = validation_info

        ctx.middleware_pre_ms += (perf_counter() - middleware_t0) * 1000
        ctx.route_started_at = perf_counter()

        if validation_info and not validation_info.get("is_valid", True):
            ctx.add_breadcrumb("validation:detected_failure")
            # Only intercept JSON/API requests; let HTML forms handle validation errors in their routes.
            if request.path.startswith("/api") or request.is_json:
                response = _build_error_response(
                    {
                        "message": "تعذر إرسال الطلب. يرجى التأكد من تعبئة جميع الحقول المطلوبة بشكل صحيح قبل الإرسال.",
                        "request_id": getattr(g, "request_id", None),
                    },
                    HTTPStatus.BAD_REQUEST,
                )
                return response

    @app.after_request
    def _finalize_logging(response: Response):
        ctx = build_logging_context()
        ctx.route_finished_at = perf_counter()
        middleware_t0 = perf_counter()

        ctx.outgoing_payload.update(capture_outgoing_response(response))
        validation_source = ctx.incoming_payload
        extracted_validation = extract_validation_state(response, validation_source)
        if ctx.validation and extracted_validation:
            ctx.validation = _merge_validation(ctx.validation, extracted_validation)
        elif extracted_validation:
            ctx.validation = extracted_validation
        ctx.validation = ctx.validation or {}
        if (
            response.status_code >= HTTPStatus.BAD_REQUEST
            and ctx.validation
            and (ctx.validation.get("failures") or extracted_validation)
        ):
            ctx.add_breadcrumb("validation:detected_failure")
        ctx.middleware_post_ms += (perf_counter() - middleware_t0) * 1000

        if not getattr(g, "_log_emitted", False):
            _emit_final_log(ctx, response.status_code)
            g._log_emitted = True

        _set_response_ids(response, request_id=ctx.request_id, trace_id=ctx.trace_id, parent_id=ctx.parent_id)
        return response

    @app.errorhandler(Exception)
    def _capture_exception(exc: Exception):
        ctx = build_logging_context()
        ctx.route_finished_at = perf_counter()
        ctx.add_breadcrumb("error_handler", file=__file__, function="_capture_exception", line=__line__())

        status = getattr(exc, "code", HTTPStatus.INTERNAL_SERVER_ERROR)
        safe_status = _coerce_status(status)
        if isinstance(exc, HTTPException):
            message = exc.description or str(exc)
        else:
            message = str(exc)

        error_payload = serialize_exception(exc)
        error_payload["payload_snapshot"] = snapshot_payload()

        response = _build_error_response(message, safe_status)
        ctx.outgoing_payload.update(capture_outgoing_response(response))
        validation_source = ctx.incoming_payload
        extracted_validation = extract_validation_state(response, validation_source)
        if ctx.validation and extracted_validation:
            ctx.validation = _merge_validation(ctx.validation, extracted_validation)
        elif extracted_validation:
            ctx.validation = extracted_validation
        ctx.validation = ctx.validation or {}

        if not getattr(g, "_log_emitted", False):
            _emit_final_log(ctx, safe_status, level="ERROR")
            g._log_emitted = True

        _set_response_ids(response, request_id=ctx.request_id, trace_id=ctx.trace_id, parent_id=ctx.parent_id)
        return response, safe_status


def _coerce_status(status: object) -> int:
    if isinstance(status, int):
        return status
    if isinstance(status, str) and status.isdigit():
        try:
            return int(status)
        except ValueError:
            pass
    return int(HTTPStatus.INTERNAL_SERVER_ERROR)


def _build_error_response(message: str | dict[str, object], status: object) -> Response:
    if isinstance(message, dict):
        payload = {**message}
    else:
        payload = {"message": message}
    payload.setdefault("request_id", getattr(g, "request_id", None))
    response = jsonify(payload)
    response.status_code = _coerce_status(status)
    return response


def _emit_final_log(ctx, status_code: int, *, level: str = "INFO") -> None:
    ctx.finalized = True
    ctx.request_id = ctx.request_id or uuid4().hex
    g.request_id = ctx.request_id
    level_value = getattr(logging, level.upper(), logging.INFO)
    is_success = status_code < HTTPStatus.BAD_REQUEST and level.upper() != "ERROR"
    if is_success:
        ctx.breadcrumbs.clear()
    payload = ctx.to_log_payload(status_code, level=level, route_finished_at=ctx.route_finished_at)
    payload.pop("normalized_payload", None)
    payload.pop("cleaned_payload", None)
    payload.pop("normalization", None)
    payload.pop("__diagnostics", None)
    if is_success:
        payload.pop("breadcrumbs", None)
    logger.log(level_value, "request_cycle", extra={"log_payload": payload})


def __line__() -> int:
    import inspect

    return inspect.currentframe().f_back.f_lineno


__all__ = ["register_logging_middleware"]
