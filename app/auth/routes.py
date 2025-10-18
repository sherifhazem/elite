"""Utility helpers for handling JWT creation and validation."""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from flask import current_app


def create_token(user_id: int) -> str:
    """Generate a signed JWT that encodes the provided user identifier."""

    secret_key = current_app.config.get("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY must be configured to issue tokens.")

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

    def _normalize_membership_level(raw_level: str) -> Optional[str]:
        """Return a valid membership level matching the allowed tiers."""

        candidate = raw_level.strip()
        if not candidate:
            return None

        for level in ALLOWED_MEMBERSHIP_LEVELS:
            if candidate.lower() == level.lower():
                return level
        return None

    @auth_bp.put("/membership")
    def update_membership_level() -> tuple:
        """Allow an authenticated user to update their membership tier."""

        token = _extract_bearer_token()
        if not token:
            return (
                jsonify({"error": "Authorization header with Bearer token is required."}),
                HTTPStatus.UNAUTHORIZED,
            )

        try:
            requester_id = decode_token(token)
        except ValueError as error:
            return jsonify({"error": str(error)}), HTTPStatus.UNAUTHORIZED

        payload = _extract_json()
        level = payload.get("membership_level")
        if not isinstance(level, str):
            return (
                jsonify({"error": "membership_level must be provided as a string."}),
                HTTPStatus.BAD_REQUEST,
            )

        normalized_level = _normalize_membership_level(level)
        if normalized_level is None:
            return (
                jsonify(
                    {
                        "error": "Invalid membership level.",
                        "allowed_levels": sorted(ALLOWED_MEMBERSHIP_LEVELS),
                    }
                ),
                HTTPStatus.BAD_REQUEST,
            )

        target_user_id = payload.get("user_id")
        if target_user_id is not None:
            try:
                target_user_id = int(target_user_id)
            except (TypeError, ValueError):
                return (
                    jsonify({"error": "user_id must be an integer when provided."}),
                    HTTPStatus.BAD_REQUEST,
                )

        if target_user_id not in (None, requester_id):
            return (
                jsonify(
                    {
                        "error": "Updating other users requires elevated privileges.",
                    }
                ),
                HTTPStatus.FORBIDDEN,
            )

        user_id = requester_id if target_user_id is None else target_user_id
        user = db.session.get(User, user_id)
        if user is None:
            return jsonify({"error": "User not found."}), HTTPStatus.NOT_FOUND

        user.update_membership_level(normalized_level)
        db.session.commit()

        response = {
            "id": user.id,
            "membership_level": user.membership_level,
            "message": "Membership level updated successfully.",
        }
        return jsonify(response), HTTPStatus.OK