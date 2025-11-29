"""Utility helpers for the Observability Layer."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Mapping

from flask import g

from .config import LOG_DIR


def ensure_log_dir() -> None:
    """Create the base logs directory when missing."""

    os.makedirs(LOG_DIR, exist_ok=True)


def current_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp with a trailing Z."""

    return datetime.utcnow().isoformat() + "Z"


def generate_request_id() -> str:
    """Create a unique request identifier."""

    return uuid.uuid4().hex


def get_request_id() -> str:
    """Return the current request id, creating one if necessary."""

    request_id = getattr(g, "request_id", None)
    if not request_id:
        request_id = generate_request_id()
        try:
            g.request_id = request_id
        except Exception:
            # Fallback for contexts where g is unavailable
            pass
    return request_id


def build_log_entry(
    *,
    level: str,
    source: str,
    module: str,
    function: str,
    event: str,
    message: str,
    details: Mapping[str, Any] | None = None,
    request_id: str | None = None,
) -> Dict[str, Any]:
    """Construct a standardized log payload."""

    normalized_details: Dict[str, Any] = {"message": message}
    if details:
        normalized_details.update(details)

    return {
        "timestamp": current_timestamp(),
        "level": level.upper(),
        "request_id": request_id or get_request_id(),
        "source": source,
        "module": module,
        "function": function,
        "event": event,
        "details": normalized_details,
    }


def append_json_line(path: str, payload: Mapping[str, Any]) -> None:
    """Persist a JSON object to the supplied path as a single line."""

    ensure_log_dir()
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
