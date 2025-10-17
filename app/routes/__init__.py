"""Blueprint definitions for the ELITE backend routes."""

from flask import Blueprint, jsonify


test_blueprint = Blueprint("test_blueprint", __name__)


@test_blueprint.route("/health", methods=["GET"])
def health_check():
    """Return a simple JSON response to confirm the service is healthy."""
    return jsonify({"status": "ok"})
