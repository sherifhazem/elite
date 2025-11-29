"""Central JSON logger used across the ELITE application."""

from __future__ import annotations

import json
import logging
from typing import Any, Mapping, Optional

from .config import BACKEND_ERROR_LOG_FILE, BACKEND_LOG_FILE
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
    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = StructuredJsonFormatter()

    backend_handler = logging.FileHandler(BACKEND_LOG_FILE, encoding="utf-8")
    backend_handler.setLevel(logging.INFO)
    backend_handler.setFormatter(formatter)

    error_handler = logging.FileHandler(BACKEND_ERROR_LOG_FILE, encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    logger.addHandler(backend_handler)
    logger.addHandler(error_handler)
    return logger


def get_logger() -> logging.Logger:
    """Return the configured backend logger instance."""

    return _configure_logger()


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
