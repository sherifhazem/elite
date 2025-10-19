"""Company portal blueprint providing role-restricted management views."""

from __future__ import annotations

from datetime import datetime
from http import HTTPStatus

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from .. import db
from ..models.offer import Offer
from ..models.redemption import Redemption
from ..models.user import User
from ..services.roles import require_role

company_portal = Blueprint(
    "company_portal",
    __name__,
    url_prefix="/company",
    template_folder="../templates/dashboard",
)


def _current_company():
    """Return the company associated with the authenticated user or abort."""

    user: User | None = getattr(g, "current_user", None)
    if user is None:
        abort(HTTPStatus.UNAUTHORIZED)
    if user.company is None:
        flash(
            "No company is linked to your account yet. Please contact an administrator.",
            "warning",
        )
        return None
    return user.company


@company_portal.route("/dashboard")
@require_role("company")
def dashboard():
    """Display a high level overview for the company account."""

    company = _current_company()
    offers = []
    if company:
        offers = (
            Offer.query.filter_by(company_id=company.id)
            .order_by(Offer.valid_until.desc())
            .limit(5)
            .all()
        )
    return render_template(
        "company_portal_dashboard.html",
        section_title="Company Dashboard",
        company=company,
        offers=offers,
    )


@company_portal.route("/offers")
@require_role("company")
def list_offers():
    """List all offers belonging to the current company."""

    company = _current_company()
    offers = []
    if company:
        offers = Offer.query.filter_by(company_id=company.id).order_by(Offer.id).all()
    return render_template(
        "company_portal_offers.html",
        section_title="My Offers",
        company=company,
        offers=offers,
    )


@company_portal.route("/offers/create", methods=["GET", "POST"])
@require_role("company")
def create_offer():
    """Allow a company to create a new offer tied to their profile."""

    company = _current_company()
    if company is None:
        return redirect(url_for("company_portal.dashboard"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        discount_raw = request.form.get("base_discount", "0").strip()
        valid_until_raw = request.form.get("valid_until", "").strip()

        if not title or not discount_raw:
            flash("Title and base discount are required.", "danger")
            return redirect(url_for("company_portal.create_offer"))

        try:
            base_discount = float(discount_raw)
        except ValueError:
            flash("Base discount must be a numeric value.", "danger")
            return redirect(url_for("company_portal.create_offer"))

        valid_until = None
        if valid_until_raw:
            try:
                valid_until = datetime.strptime(valid_until_raw, "%Y-%m-%d")
            except ValueError:
                flash("Valid until must follow YYYY-MM-DD format.", "danger")
                return redirect(url_for("company_portal.create_offer"))

        offer = Offer(
            title=title,
            base_discount=base_discount,
            valid_until=valid_until,
            company_id=company.id,
        )
        db.session.add(offer)
        db.session.commit()

        flash("Offer created successfully.", "success")
        return redirect(url_for("company_portal.list_offers"))

    return render_template(
        "company_portal_offer_form.html",
        section_title="Create Offer",
        company=company,
        offer=None,
    )


@company_portal.route("/offers/<int:offer_id>/edit", methods=["GET", "POST"])
@require_role("company")
def edit_offer(offer_id: int):
    """Allow the company to update an offer that belongs to them."""

    company = _current_company()
    if company is None:
        return redirect(url_for("company_portal.dashboard"))

    offer = Offer.query.filter_by(company_id=company.id, id=offer_id).first_or_404()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        discount_raw = request.form.get("base_discount", "0").strip()
        valid_until_raw = request.form.get("valid_until", "").strip()

        if not title or not discount_raw:
            flash("Title and base discount are required.", "danger")
            return redirect(url_for("company_portal.edit_offer", offer_id=offer_id))

        try:
            offer.base_discount = float(discount_raw)
        except ValueError:
            flash("Base discount must be numeric.", "danger")
            return redirect(url_for("company_portal.edit_offer", offer_id=offer_id))

        if valid_until_raw:
            try:
                offer.valid_until = datetime.strptime(valid_until_raw, "%Y-%m-%d")
            except ValueError:
                flash("Valid until must follow YYYY-MM-DD format.", "danger")
                return redirect(url_for("company_portal.edit_offer", offer_id=offer_id))
        else:
            offer.valid_until = None

        offer.title = title
        db.session.commit()

        flash("Offer updated successfully.", "success")
        return redirect(url_for("company_portal.list_offers"))

    return render_template(
        "company_portal_offer_form.html",
        section_title="Edit Offer",
        company=company,
        offer=offer,
    )


@company_portal.route("/redemptions", methods=["GET"])
@require_role("company")
def redemptions():
    """Render the redemption management workspace for company staff."""

    company = _current_company()
    recent = []
    if company is not None:
        recent = (
            Redemption.query.filter_by(company_id=company.id)
            .order_by(Redemption.created_at.desc())
            .limit(10)
            .all()
        )
    return render_template(
        "company_portal_redemptions.html",
        section_title="Offer Redemptions",
        company=company,
        recent_redemptions=recent,
    )


__all__ = ["company_portal"]
