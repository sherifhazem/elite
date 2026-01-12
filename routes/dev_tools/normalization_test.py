"""Development-only endpoint to inspect automatic URL normalization."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.services.access_control import admin_required

normalization_test = Blueprint("normalization_test", __name__)


@normalization_test.route("/test/normalizer", methods=["POST"])
@admin_required
def run_normalization_probe():
    """Echo back received payloads after middleware normalization."""

    cleaned = getattr(request, "cleaned", {}) or {}
    form_payload = cleaned.get("__original", {}).get("form", {}) if cleaned else {}
    json_payload = cleaned.get("__original", {}).get("json") if cleaned else None

    return (
        jsonify(
            {
                "message": "Normalization probe",
                "form": form_payload,
                "json": json_payload,
                "cleaned": {k: v for k, v in cleaned.items() if not k.startswith("__")},
            }
        ),
        200,
    )


__all__ = ["normalization_test"]
