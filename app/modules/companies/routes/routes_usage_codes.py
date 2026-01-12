"""Usage code generation routes for the company portal."""

from __future__ import annotations

from datetime import datetime
from http import HTTPStatus

from flask import jsonify, render_template

from app.models import UsageCode
from app.services.access_control import company_required
from app.services.usage_code_service import generate_usage_code, get_usage_code_settings
from app.utils.company_context import _current_company
from .. import company_portal


@company_portal.route("/usage-codes", endpoint="company_usage_codes")
@company_required
def company_usage_codes() -> str:
    """Render the usage code management screen for partners."""

    company = _current_company()
    settings = get_usage_code_settings()
    now = datetime.utcnow()
    active_code = (
        UsageCode.query.filter_by(partner_id=company.id)
        .filter(UsageCode.expires_at > now)
        .order_by(UsageCode.created_at.desc())
        .first()
    )
    return render_template(
        "companies/usage_codes.html",
        company=company,
        active_code=active_code,
        settings=settings,
    )


@company_portal.route(
    "/usage-codes/generate",
    methods=["POST"],
    endpoint="company_usage_codes_generate",
)
@company_required
def company_usage_codes_generate():
    """Generate a new usage code for the authenticated partner."""

    company = _current_company()
    usage_code = generate_usage_code(company.id)
    return (
        jsonify(
            {
                "code": usage_code.code,
                "expires_at": usage_code.expires_at.isoformat()
                if usage_code.expires_at
                else None,
                "usage_count": usage_code.usage_count,
                "max_uses_per_window": usage_code.max_uses_per_window,
            }
        ),
        HTTPStatus.CREATED,
    )


__all__ = ["company_usage_codes", "company_usage_codes_generate"]
