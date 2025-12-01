"""User CRUD blueprint providing JSON endpoints secured by RBAC."""
from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from app.core.database import db
from app.models import User
from app.services.access_control import require_role


users = Blueprint("users", __name__)


def _serialize_user(user: User) -> dict:
    """Return a dictionary representation of a user without sensitive fields."""

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "membership_level": user.membership_level,
        "joined_at": user.joined_at.isoformat() if user.joined_at else None,
    }


@users.route("/", methods=["GET"], endpoint="list_users")
@require_role("admin")
def list_users():
    """Return all users in the system."""

    users = User.query.order_by(User.id).all()
    return jsonify([_serialize_user(user) for user in users]), 200


@users.route("/", methods=["POST"], endpoint="create_user")
@require_role("admin")
def create_user():
    """Create a new user from the provided JSON payload."""

    payload = request.get_json(silent=True) or {}
    username = payload.get("username")
    email = payload.get("email")
    password = payload.get("password")
    membership_level = payload.get("membership_level")

    if not username or not email or not password:
        return jsonify({"error": "username, email, and password are required."}), 400

    user = User(username=username, email=email)
    user.set_password(password)
    if membership_level:
        user.update_membership_level(membership_level)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "User with the same username or email already exists."}), 400

    return jsonify(_serialize_user(user)), 201


@users.route("/<int:user_id>", methods=["PUT"], endpoint="update_user")
@require_role("admin")
def update_user(user_id: int):
    """Update an existing user identified by user_id."""

    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": "User not found."}), 404

    payload = request.get_json(silent=True) or {}

    username = payload.get("username")
    email = payload.get("email")
    password = payload.get("password")
    membership_level = payload.get("membership_level")

    if username is not None:
        user.username = username
    if email is not None:
        user.email = email
    if password is not None:
        user.set_password(password)
    if membership_level is not None:
        user.update_membership_level(membership_level)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "User with the same username or email already exists."}), 400

    return jsonify(_serialize_user(user)), 200


@users.route("/<int:user_id>", methods=["DELETE"], endpoint="delete_user")
@require_role("admin")
def delete_user(user_id: int):
    """Remove a user from the database."""

    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": "User not found."}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"status": "deleted"}), 200


@users.route(
    "/<int:user_id>/membership", methods=["PATCH"], endpoint="update_membership"
)
@require_role("admin")
def update_membership(user_id: int):
    """Update the membership level for a specific user."""

    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": "User not found."}), 404

    payload = request.get_json(silent=True) or {}
    membership_level = payload.get("membership_level")
    if not membership_level:
        return jsonify({"error": "membership_level is required."}), 400

    user.update_membership_level(membership_level)
    db.session.commit()

    return jsonify(_serialize_user(user)), 200


__all__ = ["users"]
