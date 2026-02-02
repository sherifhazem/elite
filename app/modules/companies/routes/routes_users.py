"""Company staff management routes."""

from __future__ import annotations

import re

from flask import flash, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError

from app.core.database import db
from app.models import Permission, User
from app.services.access_control import company_required
from app.modules.companies.routes.permissions import guard_company_staff_only_tabs
from app.modules.members.services.member_roles_service import assign_permissions
from app.utils.company_context import _current_company

from . import company_portal


ROLE_LABELS = {
    "manage_offers": "إدارة العروض",
    "manage_usage_codes": "إدارة أكواد الاستخدام",
}


def _generate_username(base: str) -> str:
    """Return a unique username derived from the provided base text."""

    cleaned = re.sub(r"[^\w\u0621-\u064A]+", "", base or "", flags=re.UNICODE)
    cleaned = cleaned or "companyuser"
    candidate = cleaned
    suffix = 1
    while User.query.filter_by(username=candidate).first():
        candidate = f"{cleaned}{suffix}"
        suffix += 1
    return candidate


def _generate_unique_email(company_id: int, phone: str) -> str:
    """Return a unique synthetic email based on company and phone."""

    base = f"{company_id}.{phone}@company.local"
    candidate = base
    suffix = 1
    while User.query.filter_by(email=candidate).first():
        candidate = f"{company_id}.{phone}.{suffix}@company.local"
        suffix += 1
    return candidate


def _get_or_create_permissions(permission_names: list[str]) -> list[Permission]:
    """Return Permission records for the provided names, creating missing ones."""

    existing = {
        perm.name: perm
        for perm in Permission.query.filter(Permission.name.in_(permission_names)).all()
    }
    result = []
    for name in permission_names:
        permission = existing.get(name)
        if permission is None:
            permission = Permission(name=name, description=ROLE_LABELS.get(name))
            db.session.add(permission)
        result.append(permission)
    return result


@company_portal.route("/users", methods=["GET", "POST"], endpoint="company_users")
@company_required
def company_users() -> str:
    """Display and create company staff accounts."""

    permission_guard = guard_company_staff_only_tabs()
    if permission_guard is not None:
        return permission_guard
    company = _current_company()

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        phone_number = (request.form.get("phone_number") or "").strip()
        password = request.form.get("password") or ""
        selected_roles = request.form.getlist("roles")
        selected_roles = [role for role in selected_roles if role in ROLE_LABELS]

        if not name or not phone_number or not password:
            flash("يرجى تعبئة الاسم ورقم الجوال وكلمة المرور.", "warning")
            return redirect(url_for("company_portal.company_users"))

        if not selected_roles:
            flash("يرجى اختيار صلاحية واحدة على الأقل.", "warning")
            return redirect(url_for("company_portal.company_users"))

        if User.query.filter_by(phone_number=phone_number).first():
            flash("رقم الجوال مستخدم مسبقًا. يرجى اختيار رقم آخر.", "danger")
            return redirect(url_for("company_portal.company_users"))

        email = _generate_unique_email(company.id, phone_number)
        username = _generate_username(name or phone_number)

        staff_user = User(
            username=username,
            email=email,
            phone_number=phone_number,
            company_id=company.id,
            role="company_staff",
            is_active=True,
        )
        staff_user.set_password(password)
        db.session.add(staff_user)
        try:
            _get_or_create_permissions(selected_roles)
            assign_permissions(staff_user, selected_roles)
        except IntegrityError:
            db.session.rollback()
            flash("تعذر إنشاء المستخدم. يرجى التحقق من البيانات والمحاولة مرة أخرى.", "danger")
            return redirect(url_for("company_portal.company_users"))

        flash("تم إنشاء المستخدم بنجاح.", "success")
        return redirect(url_for("company_portal.company_users"))

    staff_users = (
        User.query.filter_by(company_id=company.id)
        .order_by(User.id.desc())
        .all()
    )

    staff_data = []
    for user in staff_users:
        permissions = []
        if user.permissions is not None:
            try:
                permissions = [perm.name for perm in user.permissions.all()]
            except Exception:
                permissions = [perm.name for perm in user.permissions]
        staff_data.append(
            {
                "user": user,
                "permissions": permissions,
            }
        )

    return render_template(
        "companies/users.html",
        company=company,
        staff_users=staff_data,
        role_labels=ROLE_LABELS,
    )
