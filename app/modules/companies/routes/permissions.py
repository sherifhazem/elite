"""Shared permission checks for the company portal routes."""

from __future__ import annotations

from http import HTTPStatus
from typing import Optional, Tuple

from flask import flash, g, jsonify, redirect, request, url_for

from app.services.access_control import can_access


def guard_company_staff_only_tabs() -> Optional[Tuple[object, int] | object]:
    """Block company staff from accessing non-permission tabs."""

    user = getattr(g, "current_user", None)
    if getattr(user, "normalized_role", None) != "company_staff":
        return None

    if can_access(user, "manage_offers"):
        target = url_for("company_portal.company_offers_list")
    elif can_access(user, "manage_usage_codes"):
        target = url_for("company_portal.company_usage_codes")
    else:
        target = url_for("company_portal.company_users")

    message = "ليس لديك صلاحية للوصول إلى هذه الصفحة."
    wants_json = request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if wants_json:
        return jsonify({"ok": False, "message": message}), HTTPStatus.FORBIDDEN

    flash(message, "warning")
    return redirect(target)


__all__ = ["guard_company_staff_only_tabs"]
