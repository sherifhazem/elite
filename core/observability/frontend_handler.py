"""Helpers for persisting frontend observability events."""

from __future__ import annotations

from typing import Any, Mapping

from .config import FRONTEND_API_LOG_FILE, FRONTEND_ERROR_LOG_FILE, UI_EVENTS_LOG_FILE
from .logger import log_event
from .utils import append_json_line, build_log_entry


def record_frontend_error(payload: Mapping[str, Any]) -> None:
    """Persist a frontend error event to the designated log file."""

    normalized = build_log_entry(
        level="ERROR",
        source="frontend",
        module=str(payload.get("module", "frontend")),
        function=str(payload.get("function", "global_error")),
        event="frontend_error",
        message=str(payload.get("message", "Frontend error")),
        details=payload,
        request_id=payload.get("request_id"),
    )
    append_json_line(FRONTEND_ERROR_LOG_FILE, normalized)
    log_event(
        level="ERROR",
        event="frontend_error",
        source="frontend",
        module=normalized["module"],
        function=normalized["function"],
        message=normalized["details"].get("message", "Frontend error"),
        details=payload,
    )


def record_api_trace(payload: Mapping[str, Any], failure: bool = False) -> None:
    """Persist API trace information emitted by the browser."""

    normalized = build_log_entry(
        level="ERROR" if failure else "INFO",
        source="api",
        module=str(payload.get("module", "frontend_api")),
        function=str(payload.get("function", "tracked_fetch")),
        event="api_trace",
        message=str(payload.get("message", "API request trace")),
        details=payload,
        request_id=payload.get("request_id"),
    )
    append_json_line(FRONTEND_API_LOG_FILE, normalized)
    log_event(
        level=normalized["level"],
        event="api_trace",
        source="api",
        module=normalized["module"],
        function=normalized["function"],
        message=normalized["details"].get("message", "API request trace"),
        details=payload,
    )


def record_ui_event(payload: Mapping[str, Any]) -> None:
    """Persist UI interaction events emitted by the browser."""

    normalized = build_log_entry(
        level="INFO",
        source="frontend",
        module=str(payload.get("module", "ui")),
        function=str(payload.get("function", "interaction")),
        event="ui_event",
        message=str(payload.get("message", "UI event")),
        details=payload,
        request_id=payload.get("request_id"),
    )
    append_json_line(UI_EVENTS_LOG_FILE, normalized)
    log_event(
        level="INFO",
        event="ui_event",
        source="frontend",
        module=normalized["module"],
        function=normalized["function"],
        message=normalized["details"].get("message", "UI event"),
        details=payload,
    )
