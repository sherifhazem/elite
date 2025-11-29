"""Configuration helpers for the Observability Layer.

The values here are hydrated from ``Config.OBSERVABILITY_CONFIG`` to avoid
duplicating paths, log levels, and request correlation settings across the
project. All paths default to local JSON logs under ``/logs``.
"""

from __future__ import annotations

import os
from typing import Any, Dict


def _load_app_config() -> Dict[str, Any]:
    """Return the observability config declared on the Flask ``Config`` class."""

    try:  # Late import to avoid circular references during app factory setup
        from app.config import Config  # type: ignore

        return dict(getattr(Config, "OBSERVABILITY_CONFIG", {}) or {})
    except Exception:
        return {}


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_LOG_DIR = os.path.join(PROJECT_ROOT, "logs")

DEFAULT_OBSERVABILITY_CONFIG: Dict[str, Any] = {
    "LOG_DIR": DEFAULT_LOG_DIR,
    "BACKEND_LOG_FILE": os.path.join(DEFAULT_LOG_DIR, "backend.log.json"),
    "BACKEND_ERROR_LOG_FILE": os.path.join(
        DEFAULT_LOG_DIR, "backend-error.log.json"
    ),
    "FRONTEND_ERROR_LOG_FILE": os.path.join(
        DEFAULT_LOG_DIR, "frontend-errors.log.json"
    ),
    "FRONTEND_API_LOG_FILE": os.path.join(DEFAULT_LOG_DIR, "frontend-api.log.json"),
    "UI_EVENTS_LOG_FILE": os.path.join(DEFAULT_LOG_DIR, "ui-events.log.json"),
    "LOG_LEVEL": "INFO",
    "ERROR_LOG_LEVEL": "ERROR",
    "REQUEST_ID_HEADER": "X-Request-ID",
    "REQUEST_ID_LENGTH": 32,
    "HANDLER_OPTIONS": {"encoding": "utf-8"},
}

OBSERVABILITY_CONFIG: Dict[str, Any] = {
    **DEFAULT_OBSERVABILITY_CONFIG,
    **_load_app_config(),
}

LOG_DIR = OBSERVABILITY_CONFIG["LOG_DIR"]
BACKEND_LOG_FILE = OBSERVABILITY_CONFIG["BACKEND_LOG_FILE"]
BACKEND_ERROR_LOG_FILE = OBSERVABILITY_CONFIG["BACKEND_ERROR_LOG_FILE"]
FRONTEND_ERROR_LOG_FILE = OBSERVABILITY_CONFIG["FRONTEND_ERROR_LOG_FILE"]
FRONTEND_API_LOG_FILE = OBSERVABILITY_CONFIG["FRONTEND_API_LOG_FILE"]
UI_EVENTS_LOG_FILE = OBSERVABILITY_CONFIG["UI_EVENTS_LOG_FILE"]
LOG_LEVEL = str(OBSERVABILITY_CONFIG.get("LOG_LEVEL", "INFO"))
ERROR_LOG_LEVEL = str(OBSERVABILITY_CONFIG.get("ERROR_LOG_LEVEL", "ERROR"))
REQUEST_ID_HEADER = str(OBSERVABILITY_CONFIG.get("REQUEST_ID_HEADER", "X-Request-ID"))
REQUEST_ID_LENGTH = int(OBSERVABILITY_CONFIG.get("REQUEST_ID_LENGTH", 32))
HANDLER_OPTIONS = dict(OBSERVABILITY_CONFIG.get("HANDLER_OPTIONS", {}))

STANDARD_FIELDS = (
    "timestamp",
    "level",
    "request_id",
    "source",
    "module",
    "function",
    "event",
    "details",
)
"""Ordered tuple describing the required schema for all log entries."""
