"""Company settings and profile routes."""

from __future__ import annotations

from http import HTTPStatus

from flask import flash, g, jsonify, redirect, render_template, request, url_for

from app.core.database import db
from app.services.access_control import require_role
from app.modules.companies.services.company_profile_service import (
    get_notification_preferences,
)
from . import company_portal
from app.utils.company_context import _ensure_company, _current_company


@company_portal.route("/settings", methods=["GET", "POST"], endpoint="company_settings")
@require_role("company")
def company_settings():
    """Display and persist company profile metadata."""

    company = _current_company()

    if request.method == "POST":
        data = request.get_json() if request.is_json else request.form

        def _as_bool(raw_value) -> bool:
            if isinstance(raw_value, bool):
                return raw_value
            return str(raw_value).lower() in {"1", "true", "on", "yes"}

        proposed_name = (data.get("name") or "").strip()
        proposed_email = (data.get("account_email") or "").strip()
        proposed_registration = (data.get("registration_number") or "").strip()
        description = (data.get("description") or "").strip()
        logo_url = (data.get("logo_url") or "").strip()
        notifications_email = _as_bool(data.get("notify_email"))
        notifications_sms = _as_bool(data.get("notify_sms"))

        restricted_attempts = []
        if proposed_name and proposed_name != company.name:
            restricted_attempts.append("name")

        owner_email = ""
        if company.owner and getattr(company.owner, "email", None):
            owner_email = company.owner.email
        elif getattr(g, "current_user", None) and getattr(g.current_user, "email", None):
            owner_email = g.current_user.email
        if proposed_email and owner_email and proposed_email != owner_email:
            restricted_attempts.append("account_email")

        if hasattr(company, "registration_number"):
            current_registration = getattr(company, "registration_number") or ""
            if proposed_registration and proposed_registration != current_registration:
                restricted_attempts.append("registration_number")
            if not proposed_registration and current_registration:
                restricted_attempts.append("registration_number")

        if restricted_attempts:
            message = "هذا الحقل لا يمكن تعديله إلا بموافقة الإدارة."
            if request.is_json:
                return (
                    jsonify(
                        {
                            "ok": False,
                            "message": message,
                            "level": "warning",
                            "restricted": restricted_attempts,
                        }
                    ),
                    HTTPStatus.OK,
                )
            flash(message, "warning")
            return redirect(url_for("company_portal.company_settings"))

        company.description = description or None
        company.logo_url = logo_url or None
        company.notification_preferences = {
            "email": notifications_email,
            "sms": notifications_sms,
        }
        db.session.commit()

        success_message = "تم حفظ التغييرات بنجاح."
        if request.is_json:
            return jsonify({"ok": True, "message": success_message})
        flash(success_message, "success")
        return redirect(url_for("company_portal.company_settings"))

    return render_template(
        "companies/company_settings.html",
        company=company,
        preferences=get_notification_preferences(company),
    )
