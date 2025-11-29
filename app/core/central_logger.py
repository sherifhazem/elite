"""Central JSON logger that writes structured entries to /logs/app.log.json."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict

LOG_FILE_PATH = "/logs/app.log.json"


def _ensure_log_dir() -> None:
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)


class JsonLogFormatter(logging.Formatter):
    """Format log records as compact JSON dictionaries."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        timestamp = datetime.utcnow().isoformat() + "Z"
        payload: Dict[str, Any] = {
            "timestamp": timestamp,
            "level": record.levelname,
            "module": getattr(record, "module", record.name),
            "path": getattr(record, "path", None),
            "request_id": getattr(record, "request_id", None),
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "path",
                "request_id",
            }:
                payload.setdefault("extra", {})[key] = value

        return json.dumps(payload, ensure_ascii=False)


def _configure_logger() -> logging.Logger:
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
