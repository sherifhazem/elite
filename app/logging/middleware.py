"""Global middleware wiring for structured request logging."""

from __future__ import annotations

import logging
from http import HTTPStatus
from time import perf_counter
from uuid import uuid4

from flask import Flask, Response, g, jsonify, request
from werkzeug.datastructures import MultiDict
from werkzeug.exceptions import HTTPException

from .context import build_logging_context
from .enrichers import (
    capture_incoming_request,
    capture_outgoing_response,
    extract_validation_state,
    serialize_exception,
    snapshot_payload,
)
from .logger import get_logger
from core.normalization import normalize_url

logger = get_logger()


_URL_FIELDS = {"website_url", "social_url"}


def _should_normalize(key: str) -> bool:
    normalized_key = key.lower()
    return normalized_key in _URL_FIELDS or normalized_key.endswith("_url")


def _normalize_form_fields() -> tuple[dict[str, list[str]], list[dict[str, str]]]:
    """Normalize URL fields inside form submissions and return the updated mapping."""

    normalized_form: dict[str, list[str]] = {}
    normalization_events: list[dict[str, str]] = []

    if not request.form:
        return normalized_form, normalization_events

    mutable_form = MultiDict()
    for key, values in request.form.lists():
        normalized_values: list[str] = []
        for value in values:
            if _should_normalize(key):
                normalized_value = normalize_url(value)
                if normalized_value != value:
                    normalization_events.append({"field": key, "from": value, "to": normalized_value})
                normalized_values.append(normalized_value)
            else:
                normalized_values.append(value)
        for normalized_value in normalized_values:
            mutable_form.add(key, normalized_value)
        if _should_normalize(key):
            normalized_form[key] = normalized_values

    if normalization_events:
        request._cached_form = mutable_form

    return normalized_form, normalization_events


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
        ctx = build_logging_context()
        g.request_id = ctx.request_id
        g.trace_id = ctx.trace_id
        g.parent_id = ctx.parent_id
        ctx.add_breadcrumb("before_request:start")
        middleware_t0 = perf_counter()

        raw_payload = capture_incoming_request()
        normalized_form, normalization_events = _normalize_form_fields()
        if normalization_events:
            ctx.add_breadcrumb("normalization:url_fixed")
            ctx.normalization.extend(normalization_events)

        normalized_payload = capture_incoming_request()
        if normalized_form:
            normalized_payload.setdefault("normalized_fields", {})
            normalized_payload["normalized_fields"].update(normalized_form)

        ctx.incoming_payload.update(raw_payload)
        ctx.normalized_payload.update(normalized_payload)
        ctx.middleware_pre_ms += (perf_counter() - middleware_t0) * 1000
        ctx.route_started_at = perf_counter()

    @app.after_request
    def _finalize_logging(response: Response):
        ctx = build_logging_context()
        ctx.route_finished_at = perf_counter()
        middleware_t0 = perf_counter()

        ctx.add_breadcrumb("after_request:response_ready")
        ctx.outgoing_payload.update(capture_outgoing_response(response))
        validation_source = ctx.normalized_payload or ctx.incoming_payload
        ctx.validation = extract_validation_state(response, validation_source)
        if ctx.validation:
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
        if isinstance(exc, HTTPException):
            message = exc.description or str(exc)
        else:
            message = str(exc)

        error_payload = serialize_exception(exc)
        error_payload["payload_snapshot"] = snapshot_payload()

        response = _build_error_response(message, status)
        ctx.outgoing_payload.update(capture_outgoing_response(response))
        validation_source = ctx.normalized_payload or ctx.incoming_payload
        ctx.validation = extract_validation_state(response, validation_source)

        if not getattr(g, "_log_emitted", False):
            _emit_final_log(ctx, int(status), level="ERROR")
            g._log_emitted = True

        _set_response_ids(response, request_id=ctx.request_id, trace_id=ctx.trace_id, parent_id=ctx.parent_id)
        return response, status


def _build_error_response(message: str, status: int) -> Response:
    payload = {"message": message, "request_id": getattr(g, "request_id", None)}
    response = jsonify(payload)
    response.status_code = int(status)
    return response


def _emit_final_log(ctx, status_code: int, *, level: str = "INFO") -> None:
    ctx.finalized = True
    ctx.request_id = ctx.request_id or uuid4().hex
    g.request_id = ctx.request_id
    level_value = getattr(logging, level.upper(), logging.INFO)
    payload = ctx.to_log_payload(status_code, level=level, route_finished_at=ctx.route_finished_at)
    logger.log(level_value, "request_cycle", extra={"log_payload": payload})


def __line__() -> int:
    import inspect

    return inspect.currentframe().f_back.f_lineno


__all__ = ["register_logging_middleware"]
