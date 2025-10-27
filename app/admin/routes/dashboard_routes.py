"""Admin routes: dashboard overview and admin session controls."""

from __future__ import annotations

from flask import (
    Response,
    make_response,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    jsonify,
    abort,
    session,
)
from flask_login import logout_user

from app import db
from app.models import User, Company, Offer, ActivityLog
from app.services.roles import admin_required

from .. import admin


@admin.route("/logout", endpoint="admin_logout")
@admin_required
def admin_logout() -> Response:
    """تسجيل خروج الأدمن مع مسح الكوكي والجلسة."""

    logout_user()
    session.clear()

    resp = make_response(redirect(url_for("auth.login")))
    resp.delete_cookie("elite_token", path="/")
    resp.headers["Clear-Site-Data"] = '"storage"'
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"

    flash("تم تسجيل الخروج بنجاح ✅", "info")
    return resp


@admin.route("/", endpoint="dashboard_home")
@admin_required
def dashboard_home() -> str:
    """Render the admin dashboard landing page."""

    total_users = User.query.count()
    total_companies = (
        db.session.query(User.company_id)
        .filter(User.company_id.isnot(None))
        .distinct()
        .count()
    )
    total_offers = Offer.query.count()

    return render_template(
        "dashboard/index.html",
        section_title="Overview",
        active_page="overview",
        total_users=total_users,
        total_companies=total_companies,
        total_offers=total_offers,
    )


@admin.route("/dashboard", endpoint="dashboard_alias")
@admin_required
def dashboard_alias() -> Response:
    """Preserve backwards compatibility for /admin/dashboard links."""

    return redirect(url_for("admin.dashboard_home"))
