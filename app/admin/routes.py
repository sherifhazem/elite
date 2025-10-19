# LINKED: Route alignment & aliasing for registration and dashboards (no schema changes)
# Updated templates to use endpoint-based url_for; README cleaned & synced with actual routes.
"""Admin dashboard routes restricted to privileged users."""

from __future__ import annotations

from datetime import datetime
from http import HTTPStatus
from typing import Dict

from flask import (
    Blueprint,
    Response,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy.exc import IntegrityError

from .. import db
from ..models.company import Company
from ..models.offer import Offer
from ..models.user import User
from ..services.mailer import send_welcome_email
from ..services.notifications import broadcast_new_offer, ensure_welcome_notification
from ..services.roles import require_role

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin",
    template_folder="templates",
)


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

        flash(f"User '{username}' updated successfully.", "success")
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
@require_role("superadmin")
def delete_user(user_id: int) -> str:
    """Delete the specified user and redirect back to the listing."""

    user = User.query.get_or_404(user_id)
    if user.id == g.current_user.id:
        flash("You cannot delete your own account while logged in.", "warning")
        return redirect(url_for("admin.dashboard_users"))

    _guard_superadmin_modification(user)

    db.session.delete(user)
    db.session.commit()
    flash(f"User '{user.username}' deleted successfully.", "success")
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


@admin_bp.route("/companies")
@require_role("admin")
def dashboard_companies() -> str:
    """Render the company management interface showing all companies."""

    companies = Company.query.order_by(Company.id).all()
    return render_template(
        "dashboard/companies.html", section_title="Companies", companies=companies
    )


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

        flash(f"Company '{name}' updated successfully.", "success")
        return redirect(url_for("admin.dashboard_companies"))

    return render_template(
        "dashboard/company_form.html", section_title="Edit Company", company=company
    )


@admin_bp.route("/companies/delete/<int:company_id>", methods=["POST"])
@require_role("admin")
def delete_company(company_id: int) -> str:
    """Remove the selected company from the database."""

    company = Company.query.get_or_404(company_id)
    db.session.delete(company)
    db.session.commit()
    flash(f"Company '{company.name}' deleted successfully.", "success")
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


__all__ = ["admin_bp"]
