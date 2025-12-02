"""Centralized logging configuration for the ELITE Flask application."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any

from flask import Flask, g, has_request_context, request

_APP_LOGGER_NAME = "elite"
_LOGGER_INITIALIZED = False
_BASE_DIR = Path(__file__).resolve().parents[2]
LOG_FILE_PATH = _BASE_DIR / "logs" / "app.log.json"

_COLOR_MAP = {
    "DEBUG": "\033[0;37m",
    "INFO": "\033[0;36m",
    "WARNING": "\033[0;33m",
    "ERROR": "\033[0;31m",
    "CRITICAL": "\033[1;31m",
}
_RESET_COLOR = "\033[0m"


def _ensure_log_file() -> None:
    """Ensure the log directory and file exist."""

    LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE_PATH.touch(exist_ok=True)


class RequestAwareFormatter(logging.Formatter):
    """Formatter that injects request context and supports JSON output."""

    def __init__(self, *, json_output: bool = True, color: bool = False) -> None:
        super().__init__()
        self.json_output = json_output
        self.color = color

    def _enrich_with_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not has_request_context():
            return payload

        payload.setdefault("path", request.path)
        payload.setdefault("method", request.method)

        request_id = getattr(g, "request_id", None) or request.headers.get("X-Request-ID")
        if request_id:
            payload.setdefault("request_id", request_id)

        user_id = getattr(g, "user_id", None)
        current_user = getattr(g, "current_user", None)
        if current_user and getattr(current_user, "is_authenticated", False):
            user_id = getattr(current_user, "id", user_id)
        if user_id is None:
            try:
                from flask_login import current_user as login_user

                if getattr(login_user, "is_authenticated", False):
                    user_id = getattr(login_user, "id", None)
            except Exception:
                user_id = None
        if user_id is not None:
            payload.setdefault("user_id", user_id)

        return payload

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        payload = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "file": record.filename,
            "function": record.funcName,
            "line": record.lineno,
            "request_id": getattr(record, "request_id", None),
            "user_id": getattr(record, "user_id", None),
            "path": getattr(record, "path", None),
            "method": getattr(record, "method", None),
        }

        payload = self._enrich_with_request(payload)

        if self.json_output:
            return json.dumps(payload, ensure_ascii=False)

        color = _COLOR_MAP.get(record.levelname, "") if self.color else ""
        reset = _RESET_COLOR if color else ""

        parts = [
            f"{payload['timestamp']}",
            f"[{record.levelname}]",
            payload.get("message", ""),
            f"({record.filename}:{record.lineno}:{record.funcName})",
        ]

        request_bits = []
        if payload.get("method"):
            request_bits.append(payload["method"])
        if payload.get("path"):
            request_bits.append(payload["path"])
        if request_bits:
            parts.append(" ".join(request_bits))
        if payload.get("request_id"):
            parts.append(f"request_id={payload['request_id']}")
        if payload.get("user_id") is not None:
            parts.append(f"user_id={payload['user_id']}")

        return f"{color}" + " ".join(parts) + f"{reset}"


def _build_handlers() -> tuple[logging.Handler, logging.Handler]:
    formatter_json = RequestAwareFormatter(json_output=True)
    formatter_console = RequestAwareFormatter(json_output=False, color=True)

    file_handler = TimedRotatingFileHandler(
        LOG_FILE_PATH,
        when="midnight",
        interval=1,
        backupCount=4,
        encoding="utf-8",
        utc=True,
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.extMatch = re.compile(r"\d{4}-\d{2}-\d{2}")
    file_handler.setFormatter(formatter_json)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter_console)

    return file_handler, console_handler


def initialize_logging(app: Flask | None = None) -> logging.Logger:
    """Idempotently configure logging for root, Flask, and Werkzeug."""

    global _LOGGER_INITIALIZED
    if _LOGGER_INITIALIZED:
        if app is not None:
            app.logger.handlers.clear()
            app.logger.setLevel(logging.INFO)
            app.logger.propagate = True
        return get_logger()

    _ensure_log_file()

    file_handler, console_handler = _build_handlers()

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    for logger_name in (_APP_LOGGER_NAME, "flask.app", "werkzeug"):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.setLevel(logging.INFO)
        logger.propagate = True

    if app is not None:
        app.logger.handlers.clear()
        app.logger.setLevel(logging.INFO)
        app.logger.propagate = True

    _LOGGER_INITIALIZED = True
    return get_logger()


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a logger connected to the centralized pipeline."""

    if not _LOGGER_INITIALIZED:
        initialize_logging()

    logger_name = name or _APP_LOGGER_NAME
    return logging.getLogger(logger_name)


__all__ = ["initialize_logging", "get_logger", "LOG_FILE_PATH"]
