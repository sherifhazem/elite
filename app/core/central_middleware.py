"""Centralized request lifecycle middleware for the ELITE application."""

from __future__ import annotations

from http import HTTPStatus
from time import time
from uuid import uuid4

from flask import Flask, g, jsonify, request

from app.logging.logger import get_logger

logger = get_logger()

REQUEST_ID_HEADER = "X-Request-ID"


def _generate_request_id() -> str:
    """Return a new unique request identifier."""

    return uuid4().hex


def _request_context(request_id: str | None = None) -> dict:
    """Build the base context attached to every log entry."""

    return {
        "request_id": request_id or getattr(g, "request_id", None),
        "path": request.path,
        "method": request.method,
    }


def register_central_middleware(app: Flask) -> None:
    """Attach centralized observability hooks to the Flask app."""

    @app.before_request
    def start_request_logging() -> None:
        request_id = request.headers.get(REQUEST_ID_HEADER) or _generate_request_id()
        g.request_id = request_id
        g._request_started_at = time()
        logger.info("request_started", extra=_request_context(request_id))

    @app.after_request
    def end_request_logging(response):
        request_id = getattr(g, "request_id", None) or _generate_request_id()
        duration_ms = None
        if hasattr(g, "_request_started_at"):
            duration_ms = int((time() - g._request_started_at) * 1000)
        response.headers[REQUEST_ID_HEADER] = request_id
        logger.info(
            "request_completed",
            extra={**_request_context(request_id), "duration_ms": duration_ms},
        )
        return response

    @app.errorhandler(Exception)
    def handle_errors(error):  # noqa: ANN001
        request_id = getattr(g, "request_id", None) or _generate_request_id()
        g.request_id = request_id
        duration_ms = None
        if hasattr(g, "_request_started_at"):
            duration_ms = int((time() - g._request_started_at) * 1000)
        status = getattr(error, "code", HTTPStatus.INTERNAL_SERVER_ERROR)
        logger.error(
            "unhandled_exception",
            extra={
                **_request_context(request_id),
                "duration_ms": duration_ms,
                "details": {"status": int(status), "error": str(error)},
            },
        )
        response = jsonify({"message": "حدث خطأ غير متوقع", "request_id": request_id})
        response.headers[REQUEST_ID_HEADER] = request_id
        return response, status


__all__ = ["register_central_middleware", "REQUEST_ID_HEADER"]
