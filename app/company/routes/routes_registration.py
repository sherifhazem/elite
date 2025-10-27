"""Company registration and access control routes."""

from __future__ import annotations
from flask import (
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user as flask_current_user
from sqlalchemy.exc import IntegrityError

from .. import db
from ..models import Company
from ..services.roles import resolve_user_from_request
from . import company_portal


@company_portal.before_request
def _prevent_suspended_company_access():
    endpoint = request.endpoint or ""
    if not endpoint.startswith("company_portal."):
        return None

    if endpoint == "company_portal.complete_registration":
        return None

    user = getattr(g, "current_user", None) or flask_current_user
    if not getattr(user, "is_authenticated", False):
        user = resolve_user_from_request()

    if user is None or getattr(user, "role", "").strip().lower() != "company":
        return None

    company = getattr(user, "company", None)
    if company is None and getattr(user, "company_id", None):
        company = Company.query.get(user.company_id)

    if company and isinstance(company.status, str) and company.status.lower() == "suspended":
        flash("تم تعليق حساب شركتك مؤقتًا. يُرجى التواصل مع الدعم.", "danger")
        return redirect(url_for("auth.login_page"))

    return None


@company_portal.route(
    "/complete_registration/<int:company_id>",
    methods=["GET", "POST"],
    endpoint="complete_registration",
)
def complete_registration(company_id: int):
    company = Company.query.get_or_404(company_id)
    preferences = company.notification_settings()
    contact_number = getattr(company, "contact_number", None) or preferences.get(
        "contact_phone", ""
    )

    if request.method == "POST":
        company.name = (request.form.get("name") or company.name or "").strip()
        new_contact_number = (request.form.get("contact_number") or "").strip()

        if hasattr(company, "contact_number"):
            company.contact_number = new_contact_number
        else:
            updated_preferences = dict(preferences)
            updated_preferences["contact_phone"] = new_contact_number
            company.notification_preferences = updated_preferences

        company.admin_notes = None
        company.status = "pending"

        try:
            db.session.commit()
            flash("تم إعادة إرسال بيانات الشركة للمراجعة.", "success")
        except IntegrityError:
            db.session.rollback()
            flash("حدث خطأ أثناء حفظ البيانات. حاول مجددًا.", "danger")

        return redirect(url_for("auth.login_page"))

    return render_template(
        "company/complete_registration.html",
        company=company,
        contact_number=contact_number,
    )
