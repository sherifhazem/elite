"""Command dispatcher for remotely triggered actions."""
from __future__ import annotations

import importlib
import importlib.util
import logging
from typing import Any, Mapping

LOGGER = logging.getLogger(__name__)

_CAPTURE_MODULE = "EmployeeTracker.client.screenshot_capture"
_CAPTURE_CALLABLE = "capture_screenshot"
_STREAM_MODULE = f"{__package__}.live_stream"
_STREAM_CALLABLE = "start_stream"


def _load_callable(module_path: str, attribute: str):
    """Import ``module_path`` and return ``attribute``.

    This helper avoids wrapping imports with try/except by verifying the
    module specification before loading it. A descriptive log message is
    emitted if the module or attribute cannot be resolved.
    """

    spec = importlib.util.find_spec(module_path)
    if spec is None:
        raise ModuleNotFoundError(f"Module '{module_path}' is not available")

    module = importlib.import_module(module_path)
    if not hasattr(module, attribute):
        raise AttributeError(
            f"Attribute '{attribute}' not found in module '{module_path}'"
        )
    return getattr(module, attribute)


def handle_command(command: Mapping[str, Any]) -> None:
    """Decode the *command* dictionary and trigger the appropriate action."""

    action = command.get("action") or command.get("type")
    payload = command.get("payload") or {}
    if action == "capture_now":
        try:
            capture_callable = _load_callable(_CAPTURE_MODULE, _CAPTURE_CALLABLE)
        except (ModuleNotFoundError, AttributeError) as exc:
            LOGGER.error("Unable to execute capture command: %s", exc)
            return
        if isinstance(payload, Mapping):
            capture_callable(**payload)
        else:
            capture_callable()
        return

    if action == "start_stream":
        try:
            stream_callable = _load_callable(_STREAM_MODULE, _STREAM_CALLABLE)
        except (ModuleNotFoundError, AttributeError) as exc:
            LOGGER.error("Unable to start live stream: %s", exc)
            return
        if isinstance(payload, Mapping):
            stream_callable(**payload)
        else:
            stream_callable()
        return

    LOGGER.warning("Unknown command received: %s", command)
