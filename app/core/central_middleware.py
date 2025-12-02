"""Compatibility wrapper that routes legacy middleware to the logging stack."""

from __future__ import annotations

from flask import Flask

from app.logging.middleware import register_logging_middleware

REQUEST_ID_HEADER = "X-Request-ID"


def register_central_middleware(app: Flask) -> None:
    """Register the structured logging middleware used across the app."""

    register_logging_middleware(app)


__all__ = ["register_central_middleware", "REQUEST_ID_HEADER"]
