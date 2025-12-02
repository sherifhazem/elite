"""Compatibility shim mapping legacy imports to the centralized logger."""

from __future__ import annotations

from app.logging.logger import LOG_FILE_PATH, get_logger, initialize_logging

initialize_logging()
logger = get_logger()

__all__ = ["logger", "LOG_FILE_PATH", "initialize_logging", "get_logger"]
