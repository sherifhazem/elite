"""Admin routes: site settings management and dynamic list maintenance."""

from __future__ import annotations

from http import HTTPStatus
from typing import Dict

from flask import abort, flash, jsonify, redirect, render_template, request, Response, url_for
from flask_login import current_user

from app.services.access_control import admin_required
from app.modules.admin.services import settings_service
from app.modules.admin.services import admin_settings_service
from .. import admin


def _settings_success_response(list_type: str, message: str | None = None) -> Response:
    """Return a JSON response containing the refreshed list data."""

    items = settings_service.get_list(list_type)
    payload = {"status": "success", "items": items, "list_type": list_type}
    if message:
        payload["message"] = message
    return jsonify(payload)


def _settings_error_response(
    message: str, status: HTTPStatus = HTTPStatus.BAD_REQUEST, *, reason: str | None = None
) -> Response:
    """Return a JSON payload describing the failure."""

    payload = {"status": "error", "message": message}
    if reason:
        payload["reason"] = reason

    response = jsonify(payload)
    response.status_code = int(status)
    return response


def _extract_value(*keys: str) -> str:
    """Return the first non-empty value for the provided keys from request data."""

    cleaned = getattr(request, "cleaned", {}) or {}
    for key in keys:
        value = cleaned.get(key)
        if value not in (None, "", []):
            return str(value)
    return ""


def _extract_tab() -> str:
    """Normalize the requested tab with a safe default."""

    # Prioritize standard query parameters for GET requests
    tab = request.args.get("tab")

    # Fallback to cleaned context if available
    if not tab:
        cleaned = getattr(request, "cleaned", {}) or {}
        if "combined" in cleaned and isinstance(cleaned["combined"], dict):
            tab = cleaned["combined"].get("tab")
        else:
            tab = cleaned.get("tab")

    tab = (str(tab) if tab else "").strip().lower()
    return (
        tab
        if tab in {"cities", "industries", "admin_settings"}
        else "cities"
    )


def _handle_add_item(list_type: str) -> Response:
    """Shared handler for add endpoints."""

    name = _extract_value("name", "value", "label")
    if not (name or "").strip():
        return _settings_error_response("الاسم مطلوب.", reason="empty_value")
    try:
        items = settings_service.add_item(list_type, name)
    except ValueError as exc:
        return _settings_error_response(str(exc), reason="validation_failed")
    return jsonify({"status": "success", "items": items, "list_type": list_type})


def _handle_update_item(list_type: str) -> Response:
    """Shared handler for update endpoints."""

    current_value = _extract_value(
        "current_value",
        "current",
        "previous_value",
        "old_value",
        "original_value",
        "item_id",
    )
    new_name = _extract_value("name", "new_name", "value")
    if not (current_value or "").strip():
        return _settings_error_response("العنصر المطلوب مفقود.", reason="missing_target")
    if not (new_name or "").strip():
        return _settings_error_response("الاسم مطلوب.", reason="empty_value")
    try:
        items = settings_service.update_item(list_type, current_value, new_name)
    except ValueError as exc:
        return _settings_error_response(str(exc), reason="validation_failed")
    return jsonify({"status": "success", "items": items, "list_type": list_type})


def _handle_delete_item(list_type: str) -> Response:
    """Shared handler for delete endpoints."""

    target = _extract_value("name", "value", "item_id", "current_value")
    if not (target or "").strip():
        return _settings_error_response("قيمة غير صالحة للحذف.", reason="missing_target")
    try:
        items = settings_service.delete_item(list_type, target)
    except ValueError as exc:
        return _settings_error_response(str(exc), reason="validation_failed")
    return jsonify({"status": "success", "items": items, "list_type": list_type})


@admin.route("/settings", endpoint="settings_home")
@admin_required
def settings_home() -> str:
    """Render the consolidated site settings management experience."""

    selected_tab = _extract_tab()
    cities = settings_service.get_list("cities", active_only=False)
    industries = settings_service.get_list("industries", active_only=False)
    admin_settings = admin_settings_service.get_admin_settings()
    return render_template(
        "admin/settings.html",
        section_title="Site Settings",
        active_page="settings",
        cities=cities,
        industries=industries,
        admin_settings=admin_settings,
        selected_tab=selected_tab,
    )


@admin.route("/settings/add_city", methods=["POST"], endpoint="add_city")
@admin_required
def add_city() -> Response:
    """Add a city entry to the centralized registry."""

    return _handle_add_item("cities")


@admin.route("/settings/add_industry", methods=["POST"], endpoint="add_industry")
@admin_required
def add_industry() -> Response:
    """Add an industry entry to the centralized registry."""

    return _handle_add_item("industries")


@admin.route("/settings/update_city", methods=["POST"], endpoint="update_city")
@admin_required
def update_city() -> Response:
    """Rename an existing city entry."""

    return _handle_update_item("cities")


@admin.route(
    "/settings/update_industry", methods=["POST"], endpoint="update_industry"
)
@admin_required
def update_industry() -> Response:
    """Rename an existing industry entry."""

    return _handle_update_item("industries")


@admin.route("/settings/delete_city", methods=["POST"], endpoint="delete_city")
@admin_required
def delete_city() -> Response:
    """Remove a city entry from the registry."""

    return _handle_delete_item("cities")


@admin.route(
    "/settings/delete_industry", methods=["POST"], endpoint="delete_industry"
)
@admin_required
def delete_industry() -> Response:
    """Remove an industry entry from the registry."""

    return _handle_delete_item("industries")


@admin.route("/settings/roles", endpoint="site_settings_roles")
@admin_required
def site_settings_roles() -> str:
    """Render the Role Permissions management page for super administrators."""

    if not getattr(current_user, "is_superadmin", False):
        abort(HTTPStatus.FORBIDDEN)

    from app.modules.admin.services.roles_service import (
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
        "admin/dashboard/users_roles.html",
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

    from app.modules.admin.services.roles_service import (
        get_all_roles,
        get_role_permissions,
        save_role_permissions,
    )

    cleaned = getattr(request, "cleaned", {}) or {}
    if "combined" in cleaned and isinstance(cleaned["combined"], dict):
        cleaned = cleaned["combined"]

    payload = {k: v for k, v in cleaned.items() if not k.startswith("__")}
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


@admin.route("/settings/admin", methods=["POST"], endpoint="save_admin_settings")
@admin_required
def save_admin_settings() -> Response:
    """Persist admin-configurable settings such as activity rules and toggles."""

    cleaned = getattr(request, "cleaned", {}) or {}
    if "combined" in cleaned and isinstance(cleaned["combined"], dict):
        cleaned = cleaned["combined"]

    payload = cleaned or request.form or request.get_json(silent=True) or {}
    try:
        admin_settings_service.save_admin_settings(payload)
    except ValueError as exc:
        flash(str(exc), "danger")
    else:
        flash("✅ تم حفظ إعدادات الإدارة بنجاح", "success")

    return redirect(url_for("admin.settings_home", tab="admin_settings"))
