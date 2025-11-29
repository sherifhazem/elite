"""Configuration for the local Observability Layer.

All paths are kept relative to the project root and only plain-text JSON
logs are produced to satisfy the local-only requirement.
"""

from __future__ import annotations

import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")

BACKEND_LOG_FILE = os.path.join(LOG_DIR, "backend.log.json")
BACKEND_ERROR_LOG_FILE = os.path.join(LOG_DIR, "backend-error.log.json")
FRONTEND_ERROR_LOG_FILE = os.path.join(LOG_DIR, "frontend-errors.log.json")
FRONTEND_API_LOG_FILE = os.path.join(LOG_DIR, "frontend-api.log.json")
UI_EVENTS_LOG_FILE = os.path.join(LOG_DIR, "ui-events.log.json")

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
