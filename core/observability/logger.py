"""Central JSON logger used across the ELITE application."""

from __future__ import annotations

import json
import logging
from typing import Any, Mapping, Optional

from .config import (
    BACKEND_ERROR_LOG_FILE,
    BACKEND_LOG_FILE,
    ERROR_LOG_LEVEL,
    HANDLER_OPTIONS,
    LOG_LEVEL,
)
from .utils import build_log_entry, ensure_log_dir, get_request_id

_BASE_LOGGER_NAME = "observability.backend"


class StructuredJsonFormatter(logging.Formatter):
    """Formatter that emits log records using the standardized schema."""

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        message = getattr(record, "message_text", None) or record.getMessage()
        details = getattr(record, "details", None) or {}
        payload = build_log_entry(
            level=record.levelname,
            source=getattr(record, "source", "backend"),
            module=getattr(record, "module_override", record.module),
            function=getattr(record, "function_override", record.funcName),
            event=getattr(record, "event", ""),
            message=message,
            details=details,
            request_id=getattr(record, "request_id", None) or get_request_id(),
        )
        return json.dumps(payload, ensure_ascii=False)


def _configure_logger() -> logging.Logger:
    """Configure the shared backend logger with JSON FileHandlers."""

    logger = logging.getLogger(_BASE_LOGGER_NAME)
    if logger.handlers:
        return logger

    ensure_log_dir()
    logger.setLevel(getattr(logging, str(LOG_LEVEL).upper(), logging.INFO))
    logger.propagate = False

    formatter = StructuredJsonFormatter()

    backend_handler = logging.FileHandler(
        BACKEND_LOG_FILE, **(HANDLER_OPTIONS or {"encoding": "utf-8"})
    )
    backend_handler.setLevel(getattr(logging, str(LOG_LEVEL).upper(), logging.INFO))
    backend_handler.setFormatter(formatter)

    error_handler = logging.FileHandler(
        BACKEND_ERROR_LOG_FILE, **(HANDLER_OPTIONS or {"encoding": "utf-8"})
    )
    error_handler.setLevel(
        getattr(logging, str(ERROR_LOG_LEVEL).upper(), logging.ERROR)
    )
    error_handler.setFormatter(formatter)

    logger.addHandler(backend_handler)
    logger.addHandler(error_handler)
    return logger


def get_logger() -> logging.Logger:
    """Return the configured backend logger instance."""

    return _configure_logger()


def get_service_logger(module_override: Optional[str] = None) -> logging.LoggerAdapter:
    """Return a logger adapter that injects module metadata and request IDs."""

    base_logger = get_logger()
    extra = {"module_override": module_override} if module_override else {}
    return logging.LoggerAdapter(base_logger, extra)


def log_event(
    *,
    level: str = "INFO",
    event: str,
    source: str,
    module: str,
    function: str,
    message: str,
    details: Optional[Mapping[str, Any]] = None,
) -> None:
    """Emit a structured log entry following the standard schema."""

    logger = get_logger()
    normalized_level = level.upper()
    log_level_value = getattr(logging, normalized_level, logging.INFO)

    logger.log(
        log_level_value,
        message,
        extra={
            "event": event,
            "details": details or {},
            "source": source,
            "request_id": get_request_id(),
            "message_text": message,
            "module_override": module,
            "function_override": function,
        },
    )


def log_service_start(module: str, function: str, message: str, details=None) -> None:
    """Record the beginning of a service call."""

    log_event(
        level="INFO",
        event="service_start",
        source="service",
        module=module,
        function=function,
        message=message,
        details=details,
    )


def log_service_step(
    module: str,
    function: str,
    message: str,
    details=None,
    *,
    event: str = "service_step",
    level: str = "INFO",
) -> None:
    """Record a significant step inside a service operation."""

    log_event(
        level=level,
        event=event,
        source="service",
        module=module,
        function=function,
        message=message,
        details=details,
    )


def log_service_error(
    module: str,
    function: str,
    message: str,
    details=None,
    *,
    event: str = "service_error",
) -> None:
    """Record an error within a service with structured context."""

    log_event(
        level="ERROR",
        event=event,
        source="service",
        module=module,
        function=function,
        message=message,
        details=details,
    )


def log_service_success(
    module: str,
    function: str,
    message: str,
    details=None,
    *,
    event: str = "service_success",
) -> None:
    """Record the successful completion of a service operation."""

    log_event(
        level="INFO",
        event=event,
        source="service",
        module=module,
        function=function,
        message=message,
        details=details,
    )
