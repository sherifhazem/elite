"""Admin routes: site settings management and dynamic list maintenance."""

from __future__ import annotations

from http import HTTPStatus
from typing import Dict

from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request,
    jsonify,
    abort,
    Response,
)
from flask_login import current_user

from app import db
from app.models import User, Company, Offer, ActivityLog
from app.services.roles import admin_required

from ...services import settings_service
from .. import admin


def _settings_success_response(list_type: str, message: str | None = None) -> Response:
    """Return a JSON response containing the refreshed list data."""

    items = settings_service.get_list(list_type)
    payload = {"status": "success", "items": items}
    if message:
        payload["message"] = message
    return jsonify(payload)


def _settings_error_response(
    message: str, status: HTTPStatus = HTTPStatus.BAD_REQUEST
) -> Response:
    """Return a JSON payload describing the failure."""

    response = jsonify({"status": "error", "message": message})
    response.status_code = int(status)
    return response


def _extract_value(*keys: str) -> str:
    """Return the first non-empty value for the provided keys from request data."""

    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        for key in keys:
            value = payload.get(key)
            if value:
                return str(value)

    for key in keys:
        value = request.form.get(key)
        if value:
            return str(value)
    return ""


def _handle_add_item(list_type: str) -> Response:
    """Shared handler for add endpoints."""

    name = _extract_value("name", "value", "label")
    if not (name or "").strip():
        return _settings_error_response("الاسم مطلوب.")
    try:
        settings_service.add_item(list_type, name)
    except ValueError as exc:
        return _settings_error_response(str(exc))
    return _settings_success_response(list_type, "✅ تم تحديث القائمة بنجاح")


def _handle_update_item(list_type: str, item_id: str) -> Response:
    """Shared handler for update endpoints."""

    new_name = _extract_value("name", "new_name", "value")
    if not (new_name or "").strip():
        return _settings_error_response("الاسم مطلوب.")
    try:
        settings_service.update_item(list_type, item_id, new_name)
    except ValueError as exc:
        return _settings_error_response(str(exc))
    return _settings_success_response(list_type, "✅ تم تحديث القائمة بنجاح")


def _handle_delete_item(list_type: str, item_id: str) -> Response:
    """Shared handler for delete endpoints."""

    try:
        settings_service.delete_item(list_type, item_id)
    except ValueError as exc:
        return _settings_error_response(str(exc))
    return _settings_success_response(list_type, "✅ تم تحديث القائمة بنجاح")


@admin.route("/settings", endpoint="settings_home")
@admin_required
def settings_home() -> str:
    """Render the consolidated site settings management experience."""

    settings_payload = settings_service.get_all_settings()
    return render_template(
        "dashboard/settings.html",
        section_title="Site Settings",
        active_page="settings",
        settings=settings_payload,
    )


@admin.route(
    "/settings/update/<section>", methods=["POST"], endpoint="update_site_settings"
)
@admin_required
def update_site_settings(section: str) -> Response:
    """Persist updates for dropdown or general configuration sections."""

    normalized_section = (section or "").strip().lower()
    if normalized_section not in {"cities", "industries", "general"}:
        abort(HTTPStatus.NOT_FOUND)

    if current_user.normalized_role not in {"admin", "superadmin"}:
        abort(HTTPStatus.FORBIDDEN)

    try:
        if normalized_section in {"cities", "industries"}:
            payload = request.form.getlist("values")
            if not payload:
                payload = request.form.get("values", "")
            settings_service.update_settings(normalized_section, payload)
        else:
            general_data: Dict[str, object] = {
                "support_email": request.form.get("support_email", ""),
                "support_phone": request.form.get("support_phone", ""),
                "allow_company_auto_approval": request.form.get(
                    "allow_company_auto_approval"
                ),
            }
            settings_service.update_settings("general", general_data)
        flash("تم حفظ الإعدادات بنجاح ✅", "success")
    except ValueError as exc:
        flash(str(exc), "danger")

    return redirect(url_for("admin.settings_home"))


@admin.route("/settings/roles", endpoint="site_settings_roles")
@admin_required
def site_settings_roles() -> str:
    """Render the Role Permissions management page for super administrators."""

    if not getattr(current_user, "is_superadmin", False):
        abort(HTTPStatus.FORBIDDEN)

    from app.services.roles_service import (
        DEFAULT_PERMISSIONS,
        get_all_roles,
        get_role_permissions,
    )

    roles = get_all_roles()
    role_permissions = get_role_permissions()
    catalog_from_defaults = {
        permission
        for permissions in DEFAULT_PERMISSIONS.values()
        for permission in permissions
        if permission != "all_permissions"
    }
    catalog_from_storage = {
        permission
        for permissions in role_permissions.values()
        for permission in permissions
        if permission != "all_permissions"
    }
    permissions_catalog = sorted(catalog_from_defaults | catalog_from_storage)

    return render_template(
        "dashboard/users_roles.html",
        section_title="Role Permissions",
        active_page="settings",
        active_tab="roles",
        roles=roles,
        role_permissions=role_permissions,
        default_permissions=DEFAULT_PERMISSIONS,
        permissions_catalog=permissions_catalog,
    )


@admin.route("/settings/roles/save", methods=["POST"], endpoint="save_site_settings_roles")
@admin_required
def save_site_settings_roles() -> Response:
    """Persist role permission selections to Redis for the Superadmin."""

    if not getattr(current_user, "is_superadmin", False):
        abort(HTTPStatus.FORBIDDEN)

    from app.services.roles_service import (
        get_all_roles,
        get_role_permissions,
        save_role_permissions,
    )

    payload = request.get_json(silent=True) or {}
    updated_permissions = payload.get("role_permissions")
    if not isinstance(updated_permissions, dict):
        return _settings_error_response("صيغة البيانات غير صالحة.")

    known_roles = set(get_all_roles())
    existing_permissions = get_role_permissions()
    sanitized: Dict[str, list[str]] = {}
    for role_name in known_roles:
        if role_name == "superadmin":
            sanitized[role_name] = ["all_permissions"]
            continue

        values = updated_permissions.get(role_name)
        if values is None:
            existing = existing_permissions.get(role_name, [])
            sanitized[role_name] = existing
            continue
        if not isinstance(values, list):
            return _settings_error_response("صيغة الصلاحيات غير صالحة.")

        cleaned_values = sorted(
            {
                str(permission).strip()
                for permission in values
                if str(permission).strip() and str(permission).strip() != "all_permissions"
            }
        )
        sanitized[role_name] = cleaned_values

    save_role_permissions(sanitized)
    return jsonify(
        {
            "status": "success",
            "message": "✅ تم حفظ صلاحيات الأدوار بنجاح",
            "role_permissions": sanitized,
        }
    )


@admin.route("/settings/cities", methods=["GET"], endpoint="fetch_cities")
@admin_required
def fetch_cities() -> Response:
    """Return the list of managed cities as JSON."""

    return _settings_success_response("cities")


@admin.route("/settings/industries", methods=["GET"], endpoint="fetch_industries")
@admin_required
def fetch_industries() -> Response:
    """Return the list of managed industries as JSON."""

    return _settings_success_response("industries")


@admin.route("/settings/cities/add", methods=["POST"], endpoint="add_city")
@admin_required
def add_city() -> Response:
    """Add a new city entry to the managed list via JSON."""

    return _handle_add_item("cities")


@admin.route("/settings/industries/add", methods=["POST"], endpoint="add_industry")
@admin_required
def add_industry() -> Response:
    """Add a new industry entry to the managed list via JSON."""

    return _handle_add_item("industries")


@admin.route(
    "/settings/cities/update/<path:item_id>",
    methods=["POST"],
    endpoint="update_city",
)
@admin_required
def update_city(item_id: str) -> Response:
    """Rename a city entry."""

    return _handle_update_item("cities", item_id)


@admin.route(
    "/settings/industries/update/<path:item_id>",
    methods=["POST"],
    endpoint="update_industry",
)
@admin_required
def update_industry(item_id: str) -> Response:
    """Rename an industry entry."""

    return _handle_update_item("industries", item_id)


@admin.route(
    "/settings/cities/delete/<path:item_id>",
    methods=["POST"],
    endpoint="delete_city",
)
@admin_required
def delete_city(item_id: str) -> Response:
    """Remove a city entry."""

    return _handle_delete_item("cities", item_id)


@admin.route(
    "/settings/industries/delete/<path:item_id>",
    methods=["POST"],
    endpoint="delete_industry",
)
@admin_required
def delete_industry(item_id: str) -> Response:
    """Remove an industry entry."""

    return _handle_delete_item("industries", item_id)
