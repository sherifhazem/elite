"""Utility helpers for handling JWT creation and validation."""

from datetime import datetime, timedelta, timezone
from typing import Any
from importlib import import_module

from flask import current_app


def _load_jwt_module():
    """Return the PyJWT module, raising a runtime error if unavailable."""

    try:
        return import_module("jwt")
    except ModuleNotFoundError as error:  # pragma: no cover - environment safeguard
        raise RuntimeError(
            "PyJWT must be installed to generate or validate authentication tokens."
        ) from error



def create_token(user_id: int) -> str:
    """Generate a signed JWT that encodes the provided user identifier."""

    secret_key = current_app.config.get("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY must be configured to issue tokens.")
    jwt = _load_jwt_module()

    expiration = datetime.now(tz=timezone.utc) + timedelta(hours=24)
    payload = {
        "sub": str(user_id),
        "iat": datetime.now(tz=timezone.utc),
        "exp": expiration,
    }

    token = jwt.encode(payload, secret_key, algorithm="HS256")
    if isinstance(token, bytes):
        return token.decode("utf-8")
    return token


def decode_token(token: str) -> int:
    """Validate a JWT and return the encoded user identifier."""

    secret_key = current_app.config.get("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY must be configured to validate tokens.")
    jwt = _load_jwt_module()

    try:
        payload: Any = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as error:
        raise ValueError("Token has expired.") from error
    except jwt.InvalidTokenError as error:
        raise ValueError("Token is invalid.") from error

    subject = payload.get("sub")
    if subject is None:
        raise ValueError("Token payload is missing the subject claim.")

    try:
        return int(subject)
    except (TypeError, ValueError) as error:  # pragma: no cover - defensive runtime conversion
        raise ValueError("Token subject is not a valid integer identifier.") from error
