"""Admin dashboard routes restricted to privileged users."""

from __future__ import annotations

from datetime import datetime
from functools import wraps
from http import HTTPStatus
from typing import Any, Callable, TypeVar

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError

from ..auth.utils import decode_token
from .. import db
from ..models.company import Company
from ..models.offer import Offer
from ..models.user import User

F = TypeVar("F", bound=Callable[..., Any])

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin",
    template_folder="templates",
)


def _extract_bearer_token() -> str | None:
    """Return a bearer token from the Authorization header if present."""

    authorization = request.headers.get("Authorization", "").strip()
    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


def admin_required(func: F) -> F:
    """Decorator ensuring the current request originates from an admin user."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        token = _extract_bearer_token()
        if not token:
            abort(HTTPStatus.UNAUTHORIZED)

        try:
            user_id = decode_token(token)
        except ValueError:
            abort(HTTPStatus.UNAUTHORIZED)

        user = User.query.get(user_id)
        if user is None or not getattr(user, "is_admin", False):
            abort(HTTPStatus.FORBIDDEN)

        return func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


@admin_bp.route("/")
@admin_required
def dashboard_home() -> str:
    """Render the admin dashboard landing page."""

    return render_template("dashboard/index.html", section_title="Overview")


@admin_bp.route("/users")
@admin_required
def dashboard_users() -> str:
    """Render the user management interface with a table of all users."""

    users = User.query.order_by(User.id).all()
    return render_template("dashboard/users.html", section_title="Users", users=users)


@admin_bp.route("/users/add", methods=["GET", "POST"])
@admin_required
def add_user() -> str:
    """Handle rendering and submission of the create-user form."""

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        is_admin = bool(request.form.get("is_admin"))
        membership_level = request.form.get("membership_level", "Basic").strip() or "Basic"

        if not username or not email or not password:
            flash("Username, email, and password are required to create a user.", "danger")
            return redirect(url_for("admin.add_user"))

        user = User(username=username, email=email, is_admin=is_admin, membership_level=membership_level)
        user.set_password(password)

        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Username or email already exists. Please choose different values.", "danger")
            return redirect(url_for("admin.add_user"))

        flash(f"User '{username}' created successfully.", "success")
        return redirect(url_for("admin.dashboard_users"))

    return render_template("dashboard/user_form.html", section_title="Add User", user=None)


@admin_bp.route("/users/edit/<int:user_id>", methods=["GET", "POST"])
@admin_required
def edit_user(user_id: int) -> str:
    """Edit an existing user's details after validating input."""

    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        is_admin = bool(request.form.get("is_admin"))
        membership_level = request.form.get("membership_level", "Basic").strip() or "Basic"

        if not username or not email:
            flash("Username and email are required.", "danger")
            return redirect(url_for("admin.edit_user", user_id=user_id))

        user.username = username
        user.email = email
        user.is_admin = is_admin
        user.membership_level = membership_level
        if password:
            user.set_password(password)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Unable to update user. Username or email may already exist.", "danger")
            return redirect(url_for("admin.edit_user", user_id=user_id))

        flash(f"User '{username}' updated successfully.", "success")
        return redirect(url_for("admin.dashboard_users"))

    return render_template("dashboard/user_form.html", section_title="Edit User", user=user)


@admin_bp.route("/users/delete/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id: int) -> str:
    """Delete the specified user and redirect back to the listing."""

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f"User '{user.username}' deleted successfully.", "success")
    return redirect(url_for("admin.dashboard_users"))


@admin_bp.route("/companies")
@admin_required
def dashboard_companies() -> str:
    """Render the company management interface showing all companies."""

    companies = Company.query.order_by(Company.id).all()
    return render_template(
        "dashboard/companies.html", section_title="Companies", companies=companies
    )


@admin_bp.route("/companies/add", methods=["GET", "POST"])
@admin_required
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

        flash(f"Company '{name}' created successfully.", "success")
        return redirect(url_for("admin.dashboard_companies"))

    return render_template(
        "dashboard/company_form.html", section_title="Add Company", company=None
    )


@admin_bp.route("/companies/edit/<int:company_id>", methods=["GET", "POST"])
@admin_required
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
@admin_required
def delete_company(company_id: int) -> str:
    """Remove the selected company from the database."""

    company = Company.query.get_or_404(company_id)
    db.session.delete(company)
    db.session.commit()
    flash(f"Company '{company.name}' deleted successfully.", "success")
    return redirect(url_for("admin.dashboard_companies"))


@admin_bp.route("/offers")
@admin_required
def dashboard_offers() -> str:
    """Render the offer management view with current offers and related companies."""

    offers = Offer.query.order_by(Offer.id).all()
    companies = Company.query.order_by(Company.name).all()
    return render_template(
        "dashboard/offers.html",
        section_title="Offers",
        offers=offers,
        companies=companies,
    )


@admin_bp.route("/offers/add", methods=["GET", "POST"])
@admin_required
def add_offer() -> str:
    """Create a new offer tied to a company and persist it in the database."""

    companies = Company.query.order_by(Company.name).all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        discount_raw = request.form.get("discount_percent", "0").strip()
        valid_until_raw = request.form.get("valid_until", "").strip()
        company_id_raw = request.form.get("company_id", "").strip()

        if not title or not discount_raw:
            flash("Title and discount are required.", "danger")
            return redirect(url_for("admin.add_offer"))

        try:
            discount_percent = float(discount_raw)
        except ValueError:
            flash("Discount must be a numeric value.", "danger")
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
            discount_percent=discount_percent,
            valid_until=valid_until,
            company_id=company_id,
        )
        db.session.add(offer)
        db.session.commit()

        flash(f"Offer '{title}' created successfully.", "success")
        return redirect(url_for("admin.dashboard_offers"))

    return render_template(
        "dashboard/offer_form.html",
        section_title="Add Offer",
        companies=companies,
        offer=None,
    )


@admin_bp.route("/offers/edit/<int:offer_id>", methods=["GET", "POST"])
@admin_required
def edit_offer(offer_id: int) -> str:
    """Edit an existing offer's metadata and persist the updates."""

    offer = Offer.query.get_or_404(offer_id)
    companies = Company.query.order_by(Company.name).all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        discount_raw = request.form.get("discount_percent", "0").strip()
        valid_until_raw = request.form.get("valid_until", "").strip()
        company_id_raw = request.form.get("company_id", "").strip()

        if not title or not discount_raw:
            flash("Title and discount are required.", "danger")
            return redirect(url_for("admin.edit_offer", offer_id=offer_id))

        try:
            offer.discount_percent = float(discount_raw)
        except ValueError:
            flash("Discount must be a numeric value.", "danger")
            return redirect(url_for("admin.edit_offer", offer_id=offer_id))

        if valid_until_raw:
            try:
                offer.valid_until = datetime.strptime(valid_until_raw, "%Y-%m-%d")
            except ValueError:
                flash("Valid until must follow YYYY-MM-DD format.", "danger")
                return redirect(url_for("admin.edit_offer", offer_id=offer_id))
        else:
            offer.valid_until = None

        offer.title = title
        offer.company_id = int(company_id_raw) if company_id_raw else None
        if offer.company_id and Company.query.get(offer.company_id) is None:
            flash("Selected company does not exist.", "danger")
            return redirect(url_for("admin.edit_offer", offer_id=offer_id))

        db.session.commit()
        flash(f"Offer '{title}' updated successfully.", "success")
        return redirect(url_for("admin.dashboard_offers"))

    return render_template(
        "dashboard/offer_form.html",
        section_title="Edit Offer",
        offer=offer,
        companies=companies,
    )


@admin_bp.route("/offers/delete/<int:offer_id>", methods=["POST"])
@admin_required
def delete_offer(offer_id: int) -> str:
    """Delete an offer and redirect back to the offers table."""

    offer = Offer.query.get_or_404(offer_id)
    db.session.delete(offer)
    db.session.commit()
    flash(f"Offer '{offer.title}' deleted successfully.", "success")
    return redirect(url_for("admin.dashboard_offers"))
