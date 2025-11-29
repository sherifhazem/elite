"""Request-scoped middleware that emits centralized logs for every request."""

from __future__ import annotations

from http import HTTPStatus
from time import time
from uuid import uuid4

from flask import Flask, g, jsonify, request

from app.core.central_logger import logger

REQUEST_ID_HEADER = "X-Request-ID"


def _generate_request_id() -> str:
    return uuid4().hex


def _request_metadata() -> dict:
    return {
        "module": request.endpoint or request.blueprint or "app",
        "path": request.path,
    }


def register_central_middleware(app: Flask) -> None:
    """Attach before/after/error handlers for centralized observability."""

    @app.before_request
    def start_request_logging() -> None:
        request_id = request.headers.get(REQUEST_ID_HEADER) or _generate_request_id()
        g.request_id = request_id
        g._request_started_at = time()
        logger.info(
            "request_started",
            extra={"request_id": request_id, **_request_metadata()},
        )

    @app.after_request
    def end_request_logging(response):
        request_id = getattr(g, "request_id", None) or _generate_request_id()
        duration_ms = None
        if hasattr(g, "_request_started_at"):
            duration_ms = int((time() - g._request_started_at) * 1000)
        response.headers[REQUEST_ID_HEADER] = request_id
        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                **_request_metadata(),
                "duration_ms": duration_ms,
            },
        )
        return response

    @app.errorhandler(Exception)
    def handle_errors(error):  # noqa: ANN001
        request_id = getattr(g, "request_id", None) or _generate_request_id()
        g.request_id = request_id
        status = getattr(error, "code", HTTPStatus.INTERNAL_SERVER_ERROR)
        logger.error(
            str(error),
            extra={"request_id": request_id, **_request_metadata()},
        )
        return (
            jsonify({"message": "حدث خطأ غير متوقع", "request_id": request_id}),
            status,
        )


__all__ = ["register_central_middleware", "REQUEST_ID_HEADER"]
