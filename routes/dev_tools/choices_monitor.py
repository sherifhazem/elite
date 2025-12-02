from __future__ import annotations

import os

from flask import Blueprint, abort, current_app, jsonify

from core.choices import get_cities, get_industries

choices_monitor = Blueprint("choices_monitor", __name__)


@choices_monitor.route("/dev/choices", methods=["GET"])
def list_choices() -> tuple:
    """Expose the current registry values for validation and debugging."""

    env = os.getenv("FLASK_ENV") or current_app.config.get("ENV") or "production"
    if env.lower() == "production":
        abort(404)

    registry = {
        "cities": get_cities(),
        "industries": get_industries(),
    }

    return (
        jsonify({"success": True, "registry": registry, "source": "core.choices.registry"}),
        200,
    )


__all__ = ["choices_monitor"]
