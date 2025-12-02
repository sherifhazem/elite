"""Development-only endpoint to inspect automatic URL normalization."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

normalization_test = Blueprint("normalization_test", __name__)


@normalization_test.route("/test/normalizer", methods=["POST"])
def run_normalization_probe():
    """Echo back received payloads after middleware normalization."""

    form_payload = {key: request.form.getlist(key) for key in request.form.keys()}
    json_payload = request.get_json(silent=True)

    return (
        jsonify(
            {
                "message": "Normalization probe",
                "form": form_payload,
                "json": json_payload,
            }
        ),
        200,
    )


__all__ = ["normalization_test"]
