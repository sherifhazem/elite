"""Admin routes: user management (add/edit/delete/list)."""

from __future__ import annotations

from http import HTTPStatus

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
from flask import g
from sqlalchemy.exc import IntegrityError

from app.core.database import db
from app.models import User, Company, Offer, ActivityLog
from app.services.access_control import admin_required

from app.services.mailer import send_welcome_email
from app.modules.members.services.member_notifications_service import (
    ensure_welcome_notification,
)
from .. import admin


def _parse_boolean(value: str | None) -> bool:
    """Return True for typical truthy HTML form values."""

    if value is None:
        return False
    return value.lower() in {"1", "true", "on", "yes"}


def _guard_superadmin_modification(target: User) -> None:
    """Abort when a non-superadmin tries to manipulate a superadmin account."""

    actor: User | None = getattr(g, "current_user", None)
    if target.is_superadmin and (actor is None or not actor.is_superadmin):
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


@admin.route("/users", endpoint="dashboard_users")
@admin_required
def dashboard_users() -> str:
    """Render the user management interface with a table of all users."""

    users = User.query.order_by(User.id).all()
    return render_template(
        "admin/dashboard/users.html",
        section_title="Users",
        users=users,
    )


@admin.route("/users/view/<int:user_id>", endpoint="view_user")
@admin_required
def view_user(user_id: int) -> str:
    """Display read-only details for the requested user."""

    user = User.query.get_or_404(user_id)
    return render_template(
        "admin/dashboard/user_detail.html",
        section_title="View User",
        user=user,
    )


@admin.route("/users/add", methods=["GET", "POST"], endpoint="add_user")
@admin_required
def add_user() -> str:
    """Handle rendering and submission of the create-user form."""

    actor: User | None = getattr(g, "current_user", None)
    can_manage_roles = _can_manage_user_roles(actor)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        membership_level = _resolve_membership_level(
            request.form.get("membership_level", "Basic")
        )
        is_active = _parse_boolean(request.form.get("is_active"))
        desired_role = request.form.get("role", "member")

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
        "admin/dashboard/user_form.html",
        section_title="Add User",
        user=None,
        role_choices=User.ROLE_CHOICES,
        membership_choices=User.MEMBERSHIP_LEVELS,
    )


@admin.route("/users/edit/<int:user_id>", methods=["GET", "POST"], endpoint="edit_user")
@admin_required
def edit_user(user_id: int) -> str:
    """Edit an existing user's details after validating input."""

    user = User.query.get_or_404(user_id)
    _guard_superadmin_modification(user)

    actor: User | None = getattr(g, "current_user", None)
    can_manage_roles = _can_manage_user_roles(actor)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        membership_level = _resolve_membership_level(
            request.form.get("membership_level", "Basic")
        )
        is_active = _parse_boolean(request.form.get("is_active"))
        desired_role = request.form.get("role", user.role)
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
        "admin/dashboard/user_form.html",
        section_title="Edit User",
        user=user,
        role_choices=User.ROLE_CHOICES,
        membership_choices=User.MEMBERSHIP_LEVELS,
    )


@admin.route("/users/delete/<int:user_id>", methods=["POST"], endpoint="delete_user")
@admin_required
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


@admin.route("/users-roles", methods=["GET", "POST"], endpoint="manage_user_roles")
@admin_required
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
        "admin/dashboard/users_roles.html",
        section_title="Roles & Permissions",
        users=users,
        role_choices=User.ROLE_CHOICES,
        can_manage_roles=_can_manage_user_roles(getattr(g, "current_user", None)),
    )
