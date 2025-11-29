"""Request-scoped middleware for observability hooks."""

from __future__ import annotations

import time
from typing import Any

from flask import Response, g, request

from .logger import log_event
from .utils import generate_request_id, get_request_id


def init_observability(app) -> None:  # type: ignore[override]
    """Attach request lifecycle logging and request id propagation."""

    @app.before_request
    def _start_request_logging() -> None:
        if not getattr(g, "request_id", None):
            g.request_id = generate_request_id()
        g.request_started_at = time.time()
        log_event(
            level="INFO",
            event="request_start",
            source="backend",
            module=request.blueprint or "main",
            function=request.endpoint or request.method,
            message="Request started",
            details={
                "path": request.path,
                "method": request.method,
                "remote_addr": request.remote_addr,
            },
        )

    @app.after_request
    def _finalize_request_logging(response: Response) -> Response:
        request_id = get_request_id()
        response.headers["X-Request-ID"] = request_id
        duration_ms = None
        started_at = getattr(g, "request_started_at", None)
        if started_at:
            duration_ms = int((time.time() - started_at) * 1000)

        log_event(
            level="INFO",
            event="request_end",
            source="backend",
            module=request.blueprint or "main",
            function=request.endpoint or request.method,
            message="Request completed",
            details={
                "path": request.path,
                "method": request.method,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response

    @app.teardown_request
    def _teardown_request_logging(exc: Any) -> None:
        if exc:
            log_event(
                level="ERROR",
                event="request_error",
                source="backend",
                module=request.blueprint or "main",
                function=request.endpoint or request.method,
                message="Unhandled exception during request",
                details={
                    "path": request.path,
                    "method": request.method,
                    "error": str(exc),
                },
            )
