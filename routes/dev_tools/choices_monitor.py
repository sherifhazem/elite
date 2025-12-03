from __future__ import annotations

import os

from flask import Blueprint, abort, current_app, jsonify

from app.core.choices import get_cities, get_industries

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


@choices_monitor.route("/dev/settings_status", methods=["GET"])
def settings_status() -> tuple:
    """Expose the current registry status for QA in non-production environments."""

    env = os.getenv("FLASK_ENV") or current_app.config.get("ENV") or "production"
    if env.lower() == "production":
        abort(404)

    cities = get_cities()
    industries = get_industries()
    return (
        jsonify(
            {
                "cities": cities,
                "industries": industries,
                "count_cities": len(cities),
                "count_industries": len(industries),
                "source": "core.choices.registry",
                "status": "ok",
            }
        ),
        200,
    )


__all__ = ["choices_monitor"]
