"""Request-scoped logging context helpers."""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from time import perf_counter
from types import SimpleNamespace
from typing import Any, Dict, List, Optional
from uuid import uuid4

from flask import g, request


@dataclass
class LoggingContext:
    """Represents the per-request logging envelope."""

    request_id: str
    trace_id: str
    parent_id: Optional[str]
    user_id: Any
    started_at: float = field(default_factory=perf_counter)
    route_started_at: Optional[float] = None
    route_finished_at: Optional[float] = None
    middleware_pre_ms: float = 0.0
    middleware_post_ms: float = 0.0
    service_ms: float = 0.0
    breadcrumbs: List[Dict[str, Any]] = field(default_factory=list)
    incoming_payload: Dict[str, Any] = field(default_factory=dict)
    outgoing_payload: Dict[str, Any] = field(default_factory=dict)
    validation: Dict[str, Any] = field(default_factory=dict)
    finalized: bool = False

    def as_namespace(self) -> SimpleNamespace:
        """Expose a namespace bound to the Flask request for compatibility."""

        return SimpleNamespace(
            incoming_payload=self.incoming_payload,
            outgoing_payload=self.outgoing_payload,
            trace=self.breadcrumbs,
        )

    def add_breadcrumb(
        self,
        message: str,
        *,
        file: Optional[str] = None,
        function: Optional[str] = None,
        line: Optional[int] = None,
    ) -> None:
        """Append an execution breadcrumb to the request trace."""

        if file is None or function is None or line is None:
            frame = inspect.stack()[1]
            file = file or frame.filename
            function = function or frame.function
            line = line or frame.lineno

        self.breadcrumbs.append(
            {
                "file": file,
                "function": function,
                "line": line,
                "message": message,
            }
        )

    def mark_service_time(self, delta_ms: float) -> None:
        """Accumulate service decorator timing."""

        try:
            self.service_ms += float(delta_ms)
        except (TypeError, ValueError):
            pass

    def compute_timing(self, route_finished_at: Optional[float] = None) -> Dict[str, Any]:
        """Build the timing breakdown for the request lifecycle."""

        final_marker = route_finished_at or self.route_finished_at or perf_counter()
        total_ms = int((final_marker - self.started_at) * 1000)
        route_ms = None
        if self.route_started_at and (route_finished_at or self.route_finished_at):
            route_ms = max(0, int(((route_finished_at or self.route_finished_at) - self.route_started_at) * 1000))

        timing = {
            "total_ms": total_ms,
            "middleware_ms": int(self.middleware_pre_ms + self.middleware_post_ms),
            "service_ms": int(self.service_ms),
            "route_ms": route_ms,
        }
        return timing

    def to_log_payload(
        self, response_status: int, *, level: str = "INFO", route_finished_at: Optional[float] = None
    ) -> Dict[str, Any]:
        """Compose the unified log document."""

        payload: Dict[str, Any] = {
            "timestamp": None,  # set by formatter
            "level": level,
            "message": "request_cycle",
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "parent_id": self.parent_id,
            "user_id": self.user_id,
            "path": request.path,
            "method": request.method,
            "incoming_payload": self.incoming_payload,
            "outgoing_payload": self.outgoing_payload,
            "breadcrumbs": self.breadcrumbs,
            "validation": self.validation,
            "timing": self.compute_timing(route_finished_at),
            "response_status": int(response_status),
        }
        return payload


def _derive_identifier(header_key: str) -> Optional[str]:
    """Return an identifier from headers if present."""

    value = request.headers.get(header_key)
    return value if value else None


def build_logging_context() -> LoggingContext:
    """Create or fetch the request-scoped logging context."""

    if hasattr(g, "logging_context"):
        return g.logging_context

    request_id = _derive_identifier("X-Request-ID") or uuid4().hex
    trace_id = _derive_identifier("X-Trace-ID") or uuid4().hex
    parent_id = _derive_identifier("X-Parent-ID")

    user_id = getattr(g, "user_id", None)
    current_user = getattr(g, "current_user", None)
    if current_user and getattr(current_user, "is_authenticated", False):
        user_id = getattr(current_user, "id", user_id)

    ctx = LoggingContext(
        request_id=request_id,
        trace_id=trace_id,
        parent_id=parent_id,
        user_id=user_id,
    )
    g.logging_context = ctx
    g.request_id = request_id
    g.trace_id = trace_id
    g.parent_id = parent_id
    setattr(request, "meta", ctx.as_namespace())
    return ctx


__all__ = ["LoggingContext", "build_logging_context"]
