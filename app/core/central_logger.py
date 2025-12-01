"""Central JSON logger that writes structured entries to /logs/app.log.json."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict

LOG_FILE_PATH = "/logs/app.log.json"


def _ensure_log_dir() -> None:
    """Ensure the directory for the log file exists."""

    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)


def _normalize_details(details: Any) -> Dict[str, Any] | None:
    """Return a dictionary representation of details or None."""

    if details is None:
        return None
    if isinstance(details, dict):
        return details
    return {"value": details}


class JsonLogFormatter(logging.Formatter):
    """Format log records as compact JSON dictionaries."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        timestamp = datetime.utcnow().isoformat() + "Z"
        payload: Dict[str, Any] = {
            "timestamp": timestamp,
            "level": record.levelname,
            "request_id": getattr(record, "request_id", None),
            "path": getattr(record, "path", None),
            "method": getattr(record, "method", None),
            "duration_ms": getattr(record, "duration_ms", None),
            "message": record.getMessage(),
            "details": _normalize_details(getattr(record, "details", None)),
        }

        return json.dumps(payload, ensure_ascii=False)


def _configure_logger() -> logging.Logger:
    """Configure and return the centralized logger instance."""

    _ensure_log_dir()
    logger = logging.getLogger("central_logger")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
    handler.setFormatter(JsonLogFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger


logger = _configure_logger()

__all__ = ["logger", "LOG_FILE_PATH"]
