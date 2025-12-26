"""Utility helpers for handling JWT creation and validation."""

from datetime import datetime, timedelta, timezone
from importlib import import_module
from typing import Any, Optional

from flask import current_app, request
from itsdangerous import URLSafeTimedSerializer

from app.models import User


def _load_jwt_module():
    """Return the PyJWT module, raising a runtime error if unavailable."""

    try:
        return import_module("jwt")
    except ModuleNotFoundError as error:  # pragma: no cover - environment safeguard
        raise RuntimeError(
            "PyJWT must be installed to generate or validate authentication tokens."
        ) from error


def extract_bearer_token(header_value: str | None) -> Optional[str]:
    """Extract a bearer token from the provided Authorization header."""

    if not header_value:
        return None
    scheme, _, token = header_value.strip().partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token



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


# Default cookie configuration for issued authentication tokens.
AUTH_COOKIE_NAME = "elite_token"
AUTH_COOKIE_MAX_AGE = 60 * 60 * 24  # 24 hours


def _auth_cookie_parameters() -> dict[str, Any]:
    """Return standardized cookie parameters for issuing auth tokens."""

    secure_default = request.is_secure or not current_app.debug
    return {
        "key": AUTH_COOKIE_NAME,
        "max_age": current_app.config.get(
            "AUTH_COOKIE_MAX_AGE", AUTH_COOKIE_MAX_AGE
        ),
        "httponly": True,
        "secure": current_app.config.get("SESSION_COOKIE_SECURE", secure_default),
        "samesite": "Strict",
        "path": "/",
    }


def set_auth_cookie(response, token: str) -> None:
    """Attach an HttpOnly authentication cookie to the response."""

    params = _auth_cookie_parameters()
    response.set_cookie(params.pop("key"), token, **params)


def clear_auth_cookie(response) -> None:
    """Remove the authentication cookie from the client's browser."""

    params = _auth_cookie_parameters()
    response.delete_cookie(
        params.pop("key"), path=params.get("path", "/"), samesite=params.get("samesite")
    )


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


def get_user_from_token(token: str) -> Optional[User]:
    """Return User object from valid JWT token."""

    # Bail out quickly when no token is provided.
    if not token:
        return None
    try:
        user_id = decode_token(token)
    except ValueError:
        # Invalid tokens should not interrupt request handling; return None.
        return None
    # Fetch the database record associated with the decoded identifier.
    return User.query.get(user_id)


def generate_token(email: str) -> str:
    """Generate a time-sensitive confirmation token for the supplied email."""

    # ``URLSafeTimedSerializer`` signs the email with the SECRET_KEY to prevent tampering.
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    # The salt segregates confirmation tokens from any future serializer usage.
    return serializer.dumps(email, salt="email-confirm")


def confirm_token(token: str, expiration: int = 3600) -> Optional[str]:
    """Validate a confirmation token and return the original email when valid."""

    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        # ``max_age`` ensures the token expires after ``expiration`` seconds to
        # mitigate replay attempts should an email link be leaked.
        email = serializer.loads(token, salt="email-confirm", max_age=expiration)
    except Exception:
        # Any signature/expiration error results in ``None`` to signal invalid links.
        return None
    return email
