"""WebSocket listener for remote command execution.

This module establishes a persistent WebSocket connection with the
command server and delegates received payloads to the command handler.
"""
from __future__ import annotations

import json
import logging
import ssl
from typing import Any, Dict, Optional

import websocket

from .command_handler import handle_command

LOGGER = logging.getLogger(__name__)


def _should_accept_command(payload: Dict[str, Any], device_identifier: str) -> bool:
    """Return ``True`` when the payload targets the current device.

    The server is expected to include the ``target`` key with the device
    identifier (email, hostname, serial number, ...). When the key is
    omitted, the command is considered broadcast to all connected
    clients.
    """

    target = payload.get("target")
    if target is None:
        return True
    if isinstance(target, (list, tuple, set)):
        return device_identifier in target
    return target == device_identifier


def start_websocket_listener(
    server_url: str,
    device_identifier: str,
    *,
    auth_token: Optional[str] = None,
    ssl_verify: bool = True,
) -> None:
    """Connect to ``server_url`` and listen for remote commands.

    Parameters
    ----------
    server_url:
        Fully qualified WebSocket endpoint (``ws://`` أو ``wss://``).
    device_identifier:
        Unique identifier for the current device (مثل البريد أو الرقم
        التسلسلي).
    auth_token:
        اختياري. يُرسل كرأس مصادقة (Bearer token) عند إنشاء الاتصال.
    ssl_verify:
        إذا كان ``True`` يتم التحقق من شهادات TLS أثناء الاتصال.
    """

    headers = []
    if auth_token:
        headers.append(f"Authorization: Bearer {auth_token}")

    def _on_open(ws: websocket.WebSocketApp) -> None:
        LOGGER.info("WebSocket connection established with %s", server_url)
        registration_payload = json.dumps(
            {
                "action": "register_listener",
                "device": device_identifier,
            }
        )
        ws.send(registration_payload)

    def _on_message(ws: websocket.WebSocketApp, message: str) -> None:  # noqa: ARG001
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            LOGGER.error("Received invalid JSON payload: %s", message)
            return

        if not _should_accept_command(payload, device_identifier):
            LOGGER.debug(
                "Ignoring command targeted to %s", payload.get("target")
            )
            return

        command = payload.get("command")
        if not isinstance(command, dict):
            LOGGER.error("Malformed command payload: %s", payload)
            return

        LOGGER.info("Executing command: %s", command)
        handle_command(command)

    def _on_error(ws: websocket.WebSocketApp, error: Exception) -> None:  # noqa: ARG001
        LOGGER.exception("WebSocket error: %s", error)

    def _on_close(
        ws: websocket.WebSocketApp, close_status_code: int, close_msg: str
    ) -> None:  # noqa: ARG001
        LOGGER.warning(
            "WebSocket connection closed (%s): %s", close_status_code, close_msg
        )

    ws_app = websocket.WebSocketApp(
        server_url,
        header=headers,
        on_open=_on_open,
        on_message=_on_message,
        on_error=_on_error,
        on_close=_on_close,
    )

    ws_app.run_forever(
        sslopt={"cert_reqs": ssl.CERT_REQUIRED if ssl_verify else ssl.CERT_NONE}
    )
