# LINKED: Unified Logout mechanism using admin.admin_logout (GET) across all admin templates.
# Removed POST logout forms without CSRF.
# LINKED: Added “Role Permissions” page under Site Settings for Superadmin.
# Allows managing and viewing system roles stored dynamically in Redis.
# LINKED: Added comprehensive Site Settings section in Admin Panel.
# Includes Cities & Industries dynamic management integrated with Redis backend.
# LINKED: Added admin-managed dropdown system for Cities and Industries.
# Introduced unified Settings Service and admin UI for dynamic list management.
# LINKED: Fixed duplicate email error after company deletion
# Ensures orphaned company owners are cleaned up before new company registration.
# LINKED: Implemented centralized Site Settings service using Redis for dropdown and general admin configurations.
"""LINKED: Fixed admin company management actions (VIEW / EDIT / DELETE)
Added button labels and ensured correct endpoint binding and confirmation logic.

LINKED: Admin user management actions fixed (VIEW / EDIT / DELETE)
Ensured endpoints, button labels, and behavior correctness without altering layout or design.

Admin dashboard routes restricted to privileged users."""

# LINKED: Enhanced company registration form (business details + admin review integration)
# Added mandatory fields for phone, industry, city, website, and social links without schema changes.
from __future__ import annotations

from datetime import datetime
from http import HTTPStatus
from typing import Dict

from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    flash,
    g,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy.exc import IntegrityError

from flask_login import current_user, logout_user

from .. import db
from ..models.company import Company
from ..models.offer import Offer
from ..models.user import User
from ..services.mailer import (
    send_company_approval_email,
    send_company_correction_email,
    send_welcome_email,
)
from ..services.notifications import broadcast_new_offer, ensure_welcome_notification
from ..services.roles import admin_required, require_role
from ..services import settings_service

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin",
    template_folder="templates",
)




@admin_bp.route("/logout", endpoint="admin_logout")
@admin_required
def admin_logout() -> Response:
    """تسجيل خروج الأدمن مع مسح الكوكي والجلسة."""
    logout_user()
    session.clear()

    resp = make_response(redirect(url_for("auth.login")))
    # احذف كوكي الـ JWT حتى لا تتم إعادة المصادقة تلقائيًا
    resp.delete_cookie("elite_token", path="/")
    # طبقة أمان إضافية للمتصفح
    resp.headers["Clear-Site-Data"] = '"storage"'
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"

    flash("تم تسجيل الخروج بنجاح ✅", "info")
    return resp


def _parse_boolean(value: str | None) -> bool:
    """Return True for typical truthy HTML form values."""

    if value is None:
        return False
    return value.lower() in {"1", "true", "on", "yes"}


def _guard_superadmin_modification(target: User) -> None:
    """Abort when a non-superadmin tries to manipulate a superadmin account."""

    current_user: User | None = getattr(g, "current_user", None)
    if target.is_superadmin and (current_user is None or not current_user.is_superadmin):
        abort(HTTPStatus.FORBIDDEN)


def _can_manage_user_roles(actor: User | None) -> bool:
    """Return True when the acting user can update role assignments."""

    return bool(actor and actor.normalized_role in {"admin", "superadmin"})


def _can_assign_superadmin(actor: User | None) -> bool:
    """Return True when the acting user can promote others to superadmin."""

    return bool(actor and actor.is_superadmin)


def _resolve_membership_level(level: str | None) -> str:
    """Normalize the membership value from form submissions."""

    normalized = User.normalize_membership_level(level or "Basic")
    return normalized or "Basic"


def _settings_success_response(list_type: str, message: str | None = None) -> Response:
    """Return a JSON response containing the refreshed list data."""

    items = settings_service.get_list(list_type)
    payload = {"status": "success", "items": items}
    if message:
        payload["message"] = message
    return jsonify(payload)


def _settings_error_response(message: str, status: HTTPStatus = HTTPStatus.BAD_REQUEST) -> Response:
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


def _normalize_company_status(company: Company) -> str:
    """Return the normalized status string for a company record."""

    status = (company.status or "").strip().lower()
    if not status:
        return "pending"
    return status


@admin_bp.route("/")
@require_role("admin")
def dashboard_home() -> str:
    """Render the admin dashboard landing page."""

    total_users = User.query.count()
    total_companies = Company.query.count()
    total_offers = Offer.query.count()

    return render_template(
        "dashboard/index.html",
        section_title="Overview",
        total_users=total_users,
        total_companies=total_companies,
        total_offers=total_offers,
    )


@admin_bp.route("/dashboard")
@require_role("admin")
def dashboard_alias() -> Response:
    """Preserve backwards compatibility for /admin/dashboard links."""

    return redirect(url_for("admin.dashboard_home"))


@admin_bp.route("/users")
@require_role("admin")
def dashboard_users() -> str:
    """Render the user management interface with a table of all users."""

    users = User.query.order_by(User.id).all()
    return render_template(
        "dashboard/users.html",
        section_title="Users",
        users=users,
    )


@admin_bp.route("/users/view/<int:user_id>")
@require_role("admin")
def view_user(user_id: int) -> str:
    """Display read-only details for the requested user."""

    user = User.query.get_or_404(user_id)
    return render_template(
        "dashboard/user_detail.html",
        section_title="View User",
        user=user,
    )


@admin_bp.route("/users/add", methods=["GET", "POST"])
@require_role("admin")
def add_user() -> str:
    """Handle rendering and submission of the create-user form."""

    companies = Company.query.order_by(Company.name).all()
    actor: User | None = getattr(g, "current_user", None)
    can_manage_roles = _can_manage_user_roles(actor)
    can_link_company = bool(actor and actor.is_superadmin)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        membership_level = _resolve_membership_level(
            request.form.get("membership_level", "Basic")
        )
        is_active = _parse_boolean(request.form.get("is_active"))
        desired_role = request.form.get("role", "member")
        company_id_raw = request.form.get("company_id")

        if not username or not email or not password:
            flash("Username, email, and password are required to create a user.", "danger")
            return redirect(url_for("admin.add_user"))

        user = User(username=username, email=email, membership_level=membership_level)
        user.set_password(password)
        user.is_active = is_active

        if can_manage_roles:
            normalized_role = (desired_role or "member").strip().lower()
            if normalized_role == "superadmin" and not _can_assign_superadmin(actor):
                flash(
                    "Only super administrators can assign the Superadmin role.",
                    "danger",
                )
                return redirect(url_for("admin.add_user"))
            try:
                user.set_role(normalized_role)
            except ValueError as error:
                flash(str(error), "danger")
                return redirect(url_for("admin.add_user"))
            if can_link_company and company_id_raw:
                try:
                    user.company_id = int(company_id_raw)
                except ValueError:
                    user.company_id = None
        else:
            user.set_role("member")
            user.company_id = None

        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Username or email already exists. Please choose different values.", "danger")
            return redirect(url_for("admin.add_user"))

        role_key = user.normalized_role
        if role_key in {"admin", "superadmin"}:
            welcome_template = "staff"
        elif role_key == "company":
            welcome_template = "company"
        else:
            welcome_template = "member"

        send_welcome_email(
            user=user,
            template_key=welcome_template,
            company_name=getattr(getattr(user, "company", None), "name", None),
        )
        ensure_welcome_notification(user, context=welcome_template)

        flash(f"User '{username}' created successfully.", "success")
        return redirect(url_for("admin.dashboard_users"))

    return render_template(
        "dashboard/user_form.html",
        section_title="Add User",
        user=None,
        role_choices=User.ROLE_CHOICES,
        membership_choices=User.MEMBERSHIP_LEVELS,
        companies=companies,
    )


@admin_bp.route("/users/edit/<int:user_id>", methods=["GET", "POST"])
@require_role("admin")
def edit_user(user_id: int) -> str:
    """Edit an existing user's details after validating input."""

    user = User.query.get_or_404(user_id)
    _guard_superadmin_modification(user)

    companies = Company.query.order_by(Company.name).all()
    actor: User | None = getattr(g, "current_user", None)
    can_manage_roles = _can_manage_user_roles(actor)
    can_link_company = bool(actor and actor.is_superadmin)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        membership_level = _resolve_membership_level(
            request.form.get("membership_level", "Basic")
        )
        is_active = _parse_boolean(request.form.get("is_active"))
        desired_role = request.form.get("role", user.role)
        company_id_raw = request.form.get("company_id")

        if not username or not email:
            flash("Username and email are required.", "danger")
            return redirect(url_for("admin.edit_user", user_id=user_id))

        user.username = username
        user.email = email
        user.membership_level = membership_level
        user.is_active = is_active

        if password:
            user.set_password(password)

        if can_manage_roles:
            normalized_role = (desired_role or user.role).strip().lower()
            if normalized_role == "superadmin" and not _can_assign_superadmin(actor):
                flash(
                    "Only super administrators can assign the Superadmin role.",
                    "danger",
                )
                return redirect(url_for("admin.edit_user", user_id=user_id))
            try:
                user.set_role(normalized_role)
            except ValueError as error:
                flash(str(error), "danger")
                return redirect(url_for("admin.edit_user", user_id=user_id))
            if can_link_company and company_id_raw:
                try:
                    user.company_id = int(company_id_raw)
                except ValueError:
                    user.company_id = None
            else:
                user.company_id = None

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Unable to update user. Username or email may already exist.", "danger")
            return redirect(url_for("admin.edit_user", user_id=user_id))

        flash("تم تعديل بيانات المستخدم بنجاح.", "success")
        return redirect(url_for("admin.dashboard_users"))

    return render_template(
        "dashboard/user_form.html",
        section_title="Edit User",
        user=user,
        role_choices=User.ROLE_CHOICES,
        membership_choices=User.MEMBERSHIP_LEVELS,
        companies=companies,
    )


@admin_bp.route("/users/delete/<int:user_id>", methods=["POST"])
@require_role("admin")
def delete_user(user_id: int) -> str:
    """Delete the specified user and redirect back to the listing."""

    user = User.query.get_or_404(user_id)
    if user.id == g.current_user.id:
        flash("You cannot delete your own account while logged in.", "warning")
        return redirect(url_for("admin.dashboard_users"))

    if user.is_superadmin:
        flash("لا يمكن حذف مستخدم يحمل دور Superadmin.", "warning")
        return redirect(url_for("admin.dashboard_users"))

    _guard_superadmin_modification(user)

    db.session.delete(user)
    db.session.commit()
    flash("تم حذف المستخدم بنجاح.", "success")
    return redirect(url_for("admin.dashboard_users"))


@admin_bp.route("/users-roles", methods=["GET", "POST"])
@require_role("admin")
def manage_user_roles() -> str:
    """Allow administrators to review and update user roles and activation state."""

    if request.method == "POST":
        actor: User | None = getattr(g, "current_user", None)
        if not _can_manage_user_roles(actor):
            abort(HTTPStatus.FORBIDDEN)

        user_id_raw = request.form.get("user_id", "0")
        try:
            user_id = int(user_id_raw)
        except ValueError:
            flash("Invalid user identifier provided.", "danger")
            return redirect(url_for("admin.manage_user_roles"))

        target = User.query.get_or_404(user_id)
        if target.is_superadmin and not _can_assign_superadmin(actor):
            flash("Only super administrators can modify this account.", "danger")
            return redirect(url_for("admin.manage_user_roles"))

        new_role = request.form.get("role", target.role)
        is_active = _parse_boolean(request.form.get("is_active"))

        try:
            normalized_role = (new_role or target.role).strip().lower()
            if normalized_role == "superadmin" and not _can_assign_superadmin(actor):
                flash(
                    "Only super administrators can assign the Superadmin role.",
                    "danger",
                )
                return redirect(url_for("admin.manage_user_roles"))
            target.set_role(normalized_role)
        except ValueError as error:
            flash(str(error), "danger")
            return redirect(url_for("admin.manage_user_roles"))

        target.is_active = is_active
        db.session.commit()
        flash("User permissions updated successfully.", "success")
        return redirect(url_for("admin.manage_user_roles"))

    users = User.query.order_by(User.id).all()
    return render_template(
        "dashboard/users_roles.html",
        section_title="Roles & Permissions",
        users=users,
        role_choices=User.ROLE_CHOICES,
        can_manage_roles=_can_manage_user_roles(getattr(g, "current_user", None)),
    )


@admin_bp.route("/companies", methods=["GET"], endpoint="list_companies")
@admin_bp.route("/companies", methods=["GET"], endpoint="dashboard_companies")
@require_role("admin")
def list_companies() -> str:
    """Render the company management interface filtered by status."""

    requested_status = (request.args.get("status") or "pending").strip().lower()
    valid_statuses = {"pending", "approved", "correction"}
    active_tab = requested_status if requested_status in valid_statuses else "pending"

    companies = Company.query.order_by(Company.created_at.desc()).all()
    grouped: Dict[str, list[Company]] = {key: [] for key in valid_statuses}

    for company in companies:
        status = _normalize_company_status(company)
        if status not in valid_statuses:
            grouped["pending"].append(company)
        else:
            grouped[status].append(company)

    status_counts = {key: len(value) for key, value in grouped.items()}

    return render_template(
        "dashboard/companies.html",
        section_title="Companies",
        companies=grouped.get(active_tab, grouped["pending"]),
        active_tab=active_tab,
        status_counts=status_counts,
    )


@admin_bp.route("/companies/view/<int:company_id>")
@require_role("admin")
def view_company(company_id: int) -> str:
    """Display read-only details for the requested company."""

    company = Company.query.get_or_404(company_id)
    offers = sorted(
        company.offers,
        key=lambda offer: offer.created_at or datetime.min,
        reverse=True,
    )
    return render_template(
        "dashboard/company_detail.html",
        section_title="View Company",
        company=company,
        offers=offers,
    )


@admin_bp.route("/companies/review/<int:company_id>")
@admin_required
def review_company(company_id: int) -> str:
    """Show the review workspace for a pending company."""

    company = Company.query.get_or_404(company_id)
    preferences = company.notification_settings()
    return render_template(
        "dashboard/company_review.html",
        section_title="Review Company",
        company=company,
        preferences=preferences,
        status=_normalize_company_status(company),
    )


@admin_bp.route("/companies/<int:company_id>/approve", methods=["POST"])
@admin_required
def approve_company(company_id: int) -> Response:
    """Approve a pending company application."""

    company = Company.query.get_or_404(company_id)
    company.status = "approved"
    if company.owner:
        company.owner.is_active = True

    db.session.commit()

    send_company_approval_email(company)

    flash(f"Company '{company.name}' approved successfully.", "success")
    return redirect(url_for("admin.list_companies", status="pending"))


@admin_bp.route(
    "/companies/<int:company_id>/request_correction",
    methods=["POST"],
)
@admin_required
def request_company_correction(company_id: int) -> Response:
    """Request additional info or correction from company."""

    company = Company.query.get_or_404(company_id)
    notes = request.form.get("admin_notes", "").strip()
    company.admin_notes = notes
    company.status = "correction"
    db.session.commit()

    correction_link = f"{request.url_root}company/complete_registration/{company.id}"
    send_company_correction_email(company, notes, correction_link)

    contact_email = getattr(getattr(company, "owner", None), "email", "") or getattr(
        company, "email", ""
    )
    flash(
        f"Correction request sent to '{contact_email or 'company contact'}'",
        "info",
    )
    return redirect(url_for("admin.list_companies", status="pending"))


@admin_bp.route("/companies/add", methods=["GET", "POST"])
@require_role("admin")
def add_company() -> str:
    """Handle creation of a new company from admin input."""

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Company name is required.", "danger")
            return redirect(url_for("admin.add_company"))

        company = Company(name=name, description=description)
        db.session.add(company)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Company name must be unique.", "danger")
            return redirect(url_for("admin.add_company"))

        if company.owner:
            ensure_welcome_notification(company.owner, context="company")

        flash(f"Company '{name}' created successfully.", "success")
        return redirect(url_for("admin.dashboard_companies"))

    return render_template(
        "dashboard/company_form.html", section_title="Add Company", company=None
    )


@admin_bp.route("/companies/edit/<int:company_id>", methods=["GET", "POST"])
@require_role("admin")
def edit_company(company_id: int) -> str:
    """Edit an existing company's details and persist the changes."""

    company = Company.query.get_or_404(company_id)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Company name is required.", "danger")
            return redirect(url_for("admin.edit_company", company_id=company_id))

        company.name = name
        company.description = description

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Unable to update company. Name may already be in use.", "danger")
            return redirect(url_for("admin.edit_company", company_id=company_id))

        flash("تم تحديث بيانات الشركة بنجاح.", "success")
        return redirect(url_for("admin.dashboard_companies"))

    return render_template(
        "dashboard/company_form.html", section_title="Edit Company", company=company
    )


@admin_bp.route("/companies/delete/<int:company_id>", methods=["POST"])
@require_role("admin")
def delete_company(company_id: int) -> str:
    """Remove the selected company from the database."""

    company = Company.query.get_or_404(company_id)
    company.remove_owner_account()
    db.session.delete(company)
    db.session.commit()
    flash("تم حذف الشركة بنجاح.", "success")
    return redirect(url_for("admin.dashboard_companies"))


@admin_bp.route("/offers")
@require_role("admin")
def dashboard_offers() -> str:
    """Render the offer management view with dynamic membership discount previews."""

    offers = Offer.query.order_by(Offer.id).all()
    tier_styles: Dict[str, Dict[str, str]] = {
        "Basic": {"bg": "#6c757d", "text": "text-white"},
        "Silver": {"bg": "#C0C0C0", "text": "text-dark"},
        "Gold": {"bg": "#FFD700", "text": "text-dark"},
        "Premium": {"bg": "#6f42c1", "text": "text-white"},
    }
    return render_template(
        "dashboard/offers.html",
        section_title="Offers",
        offers=offers,
        tier_styles=tier_styles,
        current_time=datetime.utcnow(),
    )


@admin_bp.route("/offers/add", methods=["GET", "POST"])
@require_role("admin")
def add_offer() -> str:
    """Create a new offer tied to a company and persist it in the database."""

    companies = Company.query.order_by(Company.name).all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        discount_raw = request.form.get("base_discount", "0").strip()
        valid_until_raw = request.form.get("valid_until", "").strip()
        company_id_raw = request.form.get("company_id", "").strip()

        if not title or not discount_raw:
            flash("Title and base discount are required.", "danger")
            return redirect(url_for("admin.add_offer"))

        try:
            base_discount = float(discount_raw)
        except ValueError:
            flash("Base discount must be a numeric value.", "danger")
            return redirect(url_for("admin.add_offer"))

        valid_until = None
        if valid_until_raw:
            try:
                valid_until = datetime.strptime(valid_until_raw, "%Y-%m-%d")
            except ValueError:
                flash("Valid until must follow YYYY-MM-DD format.", "danger")
                return redirect(url_for("admin.add_offer"))

        company_id = int(company_id_raw) if company_id_raw else None
        if company_id and Company.query.get(company_id) is None:
            flash("Selected company does not exist.", "danger")
            return redirect(url_for("admin.add_offer"))

        offer = Offer(
            title=title,
            base_discount=base_discount,
            valid_until=valid_until,
            company_id=company_id,
        )
        db.session.add(offer)
        db.session.commit()

        if request.form.get("send_notifications"):
            broadcast_new_offer(offer.id)

        flash(f"Offer '{title}' created successfully.", "success")
        return redirect(url_for("admin.dashboard_offers"))

    return render_template(
        "dashboard/offer_form.html",
        section_title="Add Offer",
        companies=companies,
        offer=None,
    )


@admin_bp.route("/offers/manage/<int:offer_id>", methods=["GET", "POST"])
@require_role("admin")
def manage_offer(offer_id: int) -> str:
    """Edit an existing offer's metadata and persist the updates."""

    offer = Offer.query.get_or_404(offer_id)
    companies = Company.query.order_by(Company.name).all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        discount_raw = request.form.get("base_discount", "0").strip()
        valid_until_raw = request.form.get("valid_until", "").strip()
        company_id_raw = request.form.get("company_id", "").strip()

        if not title or not discount_raw:
            flash("Title and base discount are required.", "danger")
            return redirect(url_for("admin.manage_offer", offer_id=offer_id))

        original_base_discount = offer.base_discount
        try:
            offer.base_discount = float(discount_raw)
        except ValueError:
            flash("Base discount must be a numeric value.", "danger")
            return redirect(url_for("admin.manage_offer", offer_id=offer_id))

        if valid_until_raw:
            try:
                offer.valid_until = datetime.strptime(valid_until_raw, "%Y-%m-%d")
            except ValueError:
                flash("Valid until must follow YYYY-MM-DD format.", "danger")
                return redirect(url_for("admin.manage_offer", offer_id=offer_id))
        else:
            offer.valid_until = None

        offer.title = title
        offer.company_id = int(company_id_raw) if company_id_raw else None
        if offer.company_id and Company.query.get(offer.company_id) is None:
            flash("Selected company does not exist.", "danger")
            return redirect(url_for("admin.manage_offer", offer_id=offer_id))

        db.session.commit()
        if request.form.get("send_notifications") and offer.base_discount != original_base_discount:
            broadcast_new_offer(offer.id)

        flash(f"Offer '{title}' updated successfully.", "success")
        return redirect(url_for("admin.dashboard_offers"))

    return render_template(
        "dashboard/offer_form.html",
        section_title="Edit Offer",
        offer=offer,
        companies=companies,
    )


@admin_bp.route("/offers/edit/<int:offer_id>", methods=["GET", "POST"])
@require_role("admin")
def edit_offer_discount(offer_id: int) -> str:
    """Allow administrators to adjust the base discount for a specific offer."""

    offer = Offer.query.get_or_404(offer_id)

    if request.method == "POST":
        discount_raw = request.form.get("base_discount", "").strip()

        try:
            base_discount = float(discount_raw)
        except ValueError:
            flash("Base discount must be a numeric value.", "danger")
            return redirect(url_for("admin.edit_offer_discount", offer_id=offer_id))

        if base_discount < 0:
            flash("Base discount cannot be negative.", "danger")
            return redirect(url_for("admin.edit_offer_discount", offer_id=offer_id))

        original_base_discount = offer.base_discount
        offer.base_discount = base_discount
        db.session.commit()

        if request.form.get("send_notifications") and offer.base_discount != original_base_discount:
            broadcast_new_offer(offer.id)

        flash(
            f"Base discount for '{offer.title}' updated to {base_discount:.2f}%.",
            "success",
        )
        return redirect(url_for("admin.dashboard_offers"))

    return render_template(
        "dashboard/edit_offer_discount.html",
        section_title="Edit Discount",
        offer=offer,
    )


@admin_bp.route("/offers/delete/<int:offer_id>", methods=["POST"])
@require_role("admin")
def delete_offer(offer_id: int) -> str:
    """Delete an offer and redirect back to the offers table."""

    offer = Offer.query.get_or_404(offer_id)
    db.session.delete(offer)
    db.session.commit()
    flash(f"Offer '{offer.title}' deleted successfully.", "success")
    return redirect(url_for("admin.dashboard_offers"))


@admin_bp.route("/offers/<int:offer_id>/notify", methods=["POST"])
@require_role("admin")
def trigger_offer_notification(offer_id: int) -> str:
    """Queue a broadcast notification for the specified offer."""

    offer = Offer.query.get_or_404(offer_id)
    broadcast_new_offer(offer.id)
    flash(f"Notification broadcast queued for '{offer.title}'.", "success")
    return redirect(url_for("admin.dashboard_offers"))


@admin_bp.route("/settings", endpoint="settings_home")
@require_role("admin")
def settings_home() -> str:
    """Render the consolidated site settings management experience."""

    settings_payload = settings_service.get_all_settings()
    return render_template(
        "admin/settings/home.html",
        section_title="Site Settings",
        active_page="settings",
        settings=settings_payload,
    )


@admin_bp.route("/settings/update/<section>", methods=["POST"])
@require_role("admin")
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


@admin_bp.route("/settings/roles", endpoint="site_settings_roles")
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
        "admin/settings/roles.html",
        section_title="Role Permissions",
        active_page="settings",
        active_tab="roles",
        roles=roles,
        role_permissions=role_permissions,
        default_permissions=DEFAULT_PERMISSIONS,
        permissions_catalog=permissions_catalog,
    )


@admin_bp.route("/settings/roles/save", methods=["POST"])
@admin_required
def save_site_settings_roles() -> Response:
    """Persist role permission selections to Redis for the Superadmin."""

    if not getattr(current_user, "is_superadmin", False):
        abort(HTTPStatus.FORBIDDEN)

    from app.services.roles_service import get_all_roles, get_role_permissions, save_role_permissions

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
            "message": "تم حفظ صلاحيات الأدوار بنجاح.",
            "role_permissions": sanitized,
        }
    )


@admin_bp.route("/settings/cities", methods=["GET"])
@require_role("admin")
def fetch_cities() -> Response:
    """Return the list of managed cities as JSON."""

    return _settings_success_response("cities")


@admin_bp.route("/settings/industries", methods=["GET"])
@require_role("admin")
def fetch_industries() -> Response:
    """Return the list of managed industries as JSON."""

    return _settings_success_response("industries")


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


@admin_bp.route("/settings/cities/add", methods=["POST"])
@require_role("admin")
def add_city() -> Response:
    """Add a new city entry to the managed list via JSON."""

    return _handle_add_item("cities")


@admin_bp.route("/settings/industries/add", methods=["POST"])
@require_role("admin")
def add_industry() -> Response:
    """Add a new industry entry to the managed list via JSON."""

    return _handle_add_item("industries")


@admin_bp.route("/settings/cities/update/<path:item_id>", methods=["POST"])
@require_role("admin")
def update_city(item_id: str) -> Response:
    """Rename a city entry."""

    return _handle_update_item("cities", item_id)


@admin_bp.route("/settings/industries/update/<path:item_id>", methods=["POST"])
@require_role("admin")
def update_industry(item_id: str) -> Response:
    """Rename an industry entry."""

    return _handle_update_item("industries", item_id)


@admin_bp.route("/settings/cities/delete/<path:item_id>", methods=["POST"])
@require_role("admin")
def delete_city(item_id: str) -> Response:
    """Remove a city entry."""

    return _handle_delete_item("cities", item_id)


@admin_bp.route("/settings/industries/delete/<path:item_id>", methods=["POST"])
@require_role("admin")
def delete_industry(item_id: str) -> Response:
    """Remove an industry entry."""

    return _handle_delete_item("industries", item_id)


__all__ = ["admin_bp"]
