"""User CRUD blueprint providing JSON endpoints."""

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from .. import db
from ..models.user import User


user_routes = Blueprint("user_routes", __name__)


def _serialize_user(user: User) -> dict:
    """Return a dictionary representation of a user without sensitive fields."""

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "joined_at": user.joined_at.isoformat() if user.joined_at else None,
    }


@user_routes.route("/", methods=["GET"])
def list_users():
    """Return all users in the system."""

    users = User.query.order_by(User.id).all()
    return jsonify([_serialize_user(user) for user in users]), 200


@user_routes.route("/", methods=["POST"])
def create_user():
    """Create a new user from the provided JSON payload."""

    payload = request.get_json(silent=True) or {}
    username = payload.get("username")
    email = payload.get("email")
    password_hash = payload.get("password_hash")

    if not username or not email or not password_hash:
        return jsonify({"error": "username, email, and password_hash are required."}), 400

    user = User(username=username, email=email, password_hash=password_hash)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "User with the same username or email already exists."}), 400

    return jsonify(_serialize_user(user)), 201


@user_routes.route("/<int:user_id>", methods=["PUT"])
def update_user(user_id: int):
    """Update an existing user identified by user_id."""

    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": "User not found."}), 404

    payload = request.get_json(silent=True) or {}

    username = payload.get("username")
    email = payload.get("email")
    password_hash = payload.get("password_hash")

    if username is not None:
        user.username = username
    if email is not None:
        user.email = email
    if password_hash is not None:
        user.password_hash = password_hash

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "User with the same username or email already exists."}), 400

    return jsonify(_serialize_user(user)), 200


@user_routes.route("/<int:user_id>", methods=["DELETE"])
def delete_user(user_id: int):
    """Remove a user from the database."""

    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": "User not found."}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"status": "deleted"}), 200


__all__ = ["user_routes"]
