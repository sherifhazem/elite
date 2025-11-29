"""Application-wide routes for frontend observability ingestion."""

from __future__ import annotations

from datetime import datetime
from http import HTTPStatus

from flask import Blueprint, jsonify, request

from core.observability.frontend_handler import (
    record_api_trace,
    record_frontend_error,
    record_ui_event,
)
from core.observability.utils import get_request_id

observability = Blueprint("observability", __name__, url_prefix="/log")


@observability.route("/frontend-error", methods=["POST"])
def log_frontend_error() -> tuple:
    """Capture frontend JavaScript errors and persist them to disk."""

    payload = request.get_json(silent=True) or {}
    payload.setdefault("timestamp", datetime.utcnow().isoformat() + "Z")
    payload.setdefault("page_url", request.headers.get("Referer", request.url))
    payload["request_id"] = get_request_id()
    record_frontend_error(payload)
    return (
        jsonify({"status": "logged", "request_id": payload["request_id"]}),
        HTTPStatus.CREATED,
    )


@observability.route("/api-trace", methods=["POST"])
def log_api_trace() -> tuple:
    """Capture API tracing information from the browser."""

    payload = request.get_json(silent=True) or {}
    payload.setdefault("timestamp", datetime.utcnow().isoformat() + "Z")
    payload["request_id"] = get_request_id()
    status_code = int(payload.get("status", 0) or 0)
    record_api_trace(payload, failure=status_code >= 400)
    return (
        jsonify({"status": "logged", "request_id": payload["request_id"]}),
        HTTPStatus.CREATED,
    )


@observability.route("/ui-event", methods=["POST"])
def log_ui_event() -> tuple:
    """Capture significant UI events for local observability."""

    payload = request.get_json(silent=True) or {}
    payload.setdefault("timestamp", datetime.utcnow().isoformat() + "Z")
    payload["request_id"] = get_request_id()
    record_ui_event(payload)
    return (
        jsonify({"status": "logged", "request_id": payload["request_id"]}),
        HTTPStatus.CREATED,
    )


__all__ = ["observability"]
