"""Company settings and profile routes."""

from __future__ import annotations

from http import HTTPStatus

import os
from datetime import datetime

from flask import (
    current_app,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.utils import secure_filename

from app.core.database import db
from app.services.access_control import require_role
from app.modules.companies.services.company_profile_service import (
    get_notification_preferences,
)
from . import company_portal
from app.utils.company_context import _current_company


ALLOWED_LOGO_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "svg"}


def _wants_json(req: request) -> bool:
    """Return True when the request prefers a JSON response."""

    accepts_json = req.accept_mimetypes["application/json"] >= req.accept_mimetypes[
        "text/html"
    ]
    return req.is_json or accepts_json or req.headers.get("X-Requested-With") == "XMLHttpRequest"


def _save_logo_file(upload, company) -> str:
    """Persist the uploaded logo file and return the public URL."""

    if upload is None or upload.filename == "":
        return company.logo_url or ""

    filename = secure_filename(upload.filename)
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension not in ALLOWED_LOGO_EXTENSIONS:
        raise ValueError("صيغة الملف غير مدعومة. الرجاء رفع PNG أو JPG أو WEBP.")

    max_bytes = 2 * 1024 * 1024
    if upload.content_length and upload.content_length > max_bytes:
        raise ValueError("حجم الملف يتجاوز الحد المسموح (2MB).")

    target_dir = os.path.join(
        current_app.root_path,
        "modules",
        "companies",
        "static",
        "companies",
        "uploads",
        str(company.id),
    )
    os.makedirs(target_dir, exist_ok=True)

    stored_name = f"logo.{extension}"
    target_path = os.path.join(target_dir, stored_name)
    upload.save(target_path)

    cache_bust = int(datetime.utcnow().timestamp())
    return f"/static/companies/uploads/{company.id}/{stored_name}?v={cache_bust}"


@company_portal.route("/settings", methods=["GET", "POST"], endpoint="company_settings")
@require_role("company")
def company_settings():
    """Display and persist company profile metadata."""

    company = _current_company()

    if request.method == "POST":
        cleaned = getattr(request, "cleaned", {}) or {}
        data = {k: v for k, v in cleaned.items() if not k.startswith("__")}

        def _as_bool(raw_value) -> bool:
            if isinstance(raw_value, bool):
                return raw_value
            return str(raw_value).lower() in {"1", "true", "on", "yes"}

        proposed_name = (data.get("name") or "").strip()
        proposed_email = (data.get("account_email") or "").strip()
        proposed_registration = (data.get("registration_number") or "").strip()
        description = (data.get("description") or "").strip()
        logo_upload = request.files.get("logo_file")
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
            if _wants_json(request):
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

        try:
            saved_logo_url = _save_logo_file(logo_upload, company)
        except ValueError as exc:
            error_message = str(exc)
            if _wants_json(request):
                return jsonify({"ok": False, "message": error_message}), HTTPStatus.BAD_REQUEST
            flash(error_message, "danger")
            return redirect(url_for("company_portal.company_settings"))

        company.description = description or None
        company.logo_url = saved_logo_url or company.logo_url
        company.notification_preferences = {
            "email": notifications_email,
            "sms": notifications_sms,
        }
        db.session.commit()

        success_message = "تم حفظ التغييرات بنجاح."
        if _wants_json(request):
            return jsonify({"ok": True, "message": success_message, "logo_url": company.logo_url})
        flash(success_message, "success")
        return redirect(url_for("company_portal.company_settings"))

    return render_template(
        "companies/company_settings.html",
        company=company,
        preferences=get_notification_preferences(company),
    )
