"""Usage code generation routes for the company portal."""

from __future__ import annotations

from datetime import datetime
from http import HTTPStatus

from flask import flash, g, jsonify, redirect, render_template, request, url_for
from sqlalchemy import or_

from app.models import UsageCode
from app.services.access_control import can_access, company_required
from app.services.usage_code_service import generate_usage_code, get_usage_code_settings
from app.utils.company_context import _current_company
from .. import company_portal


@company_portal.route("/usage-codes", endpoint="company_usage_codes")
@company_required
def company_usage_codes() -> str:
    """Render the usage code management screen for partners."""

    if not can_access(getattr(g, "current_user", None), "manage_usage_codes"):
        if request.is_json:
            return (
                jsonify({"ok": False, "message": "ليس لديك صلاحية إدارة أكواد الاستخدام."}),
                HTTPStatus.FORBIDDEN,
            )
        flash("ليس لديك صلاحية إدارة أكواد الاستخدام.", "warning")
        return redirect(url_for("company_portal.company_users"))
    company = _current_company()
    settings = get_usage_code_settings()
    now = datetime.utcnow()
    active_code = (
        UsageCode.query.filter_by(partner_id=company.id)
        .filter(or_(UsageCode.expires_at.is_(None), UsageCode.expires_at > now))
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

    if not can_access(getattr(g, "current_user", None), "manage_usage_codes"):
        return (
            jsonify({"ok": False, "message": "ليس لديك صلاحية إدارة أكواد الاستخدام."}),
            HTTPStatus.FORBIDDEN,
        )
    company = _current_company()
    if company.status == "correction":
        return (
            jsonify(
                {
                    "error": "Account suspended",
                    "message": "الحساب معلق جزئيا. فضلا استكمال الاجرائات المطلوبه لتفعيل الحساب",
                }
            ),
            HTTPStatus.FORBIDDEN,
        )
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


@company_portal.route(
    "/usage-codes/current",
    methods=["GET"],
    endpoint="company_usage_codes_current",
)
@company_required
def company_usage_codes_current():
    """Fetch the current usage code for the authenticated partner."""

    if not can_access(getattr(g, "current_user", None), "manage_usage_codes"):
        return (
            jsonify({"ok": False, "message": "ليس لديك صلاحية إدارة أكواد الاستخدام."}),
            HTTPStatus.FORBIDDEN,
        )
    company = _current_company()
    if company.status == "correction":
        return (
            jsonify(
                {
                    "error": "Account suspended",
                    "message": "الحساب معلق جزئيا. فضلا استكمال الاجرائات المطلوبه لتفعيل الحساب",
                }
            ),
            HTTPStatus.FORBIDDEN,
        )

    now = datetime.utcnow()
    active_code = (
        UsageCode.query.filter_by(partner_id=company.id)
        .filter(or_(UsageCode.expires_at.is_(None), UsageCode.expires_at > now))
        .order_by(UsageCode.created_at.desc())
        .first()
    )

    if active_code is None:
        active_code = generate_usage_code(company.id)

    return jsonify(
        {
            "code": active_code.code,
            "expires_at": active_code.expires_at.isoformat()
            if active_code.expires_at
            else None,
            "usage_count": active_code.usage_count,
            "max_uses_per_window": active_code.max_uses_per_window,
        }
    )


__all__ = [
    "company_usage_codes",
    "company_usage_codes_generate",
    "company_usage_codes_current",
]
