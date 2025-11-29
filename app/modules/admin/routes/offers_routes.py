"""Admin routes: offers listing, CRUD operations, and notifications."""

from __future__ import annotations

from datetime import datetime
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

from app.core.database import db
from app.models import User, Company, Offer, ActivityLog
from app.services.access_control import admin_required

from app.modules.members.services.notifications import broadcast_new_offer
from .. import admin


@admin.route("/offers", endpoint="dashboard_offers")
@admin_required
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


@admin.route("/offers/add", methods=["GET", "POST"], endpoint="add_offer")
@admin_required
def add_offer() -> str:
    """Create a new offer tied to a company and persist it in the database."""

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        discount_raw = request.form.get("base_discount", "0").strip()
        valid_until_raw = request.form.get("valid_until", "").strip()

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

        offer = Offer(
            title=title,
            base_discount=base_discount,
            valid_until=valid_until,
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
        offer=None,
    )


@admin.route(
    "/offers/manage/<int:offer_id>", methods=["GET", "POST"], endpoint="manage_offer"
)
@admin_required
def manage_offer(offer_id: int) -> str:
    """Edit an existing offer's metadata and persist the updates."""

    offer = Offer.query.get_or_404(offer_id)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        discount_raw = request.form.get("base_discount", "0").strip()
        valid_until_raw = request.form.get("valid_until", "").strip()

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

        db.session.commit()
        if request.form.get("send_notifications") and offer.base_discount != original_base_discount:
            broadcast_new_offer(offer.id)

        flash(f"Offer '{title}' updated successfully.", "success")
        return redirect(url_for("admin.dashboard_offers"))

    return render_template(
        "dashboard/offer_form.html",
        section_title="Edit Offer",
        offer=offer,
    )


@admin.route(
    "/offers/edit/<int:offer_id>", methods=["GET", "POST"], endpoint="edit_offer_discount"
)
@admin_required
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


@admin.route("/offers/delete/<int:offer_id>", methods=["POST"], endpoint="delete_offer")
@admin_required
def delete_offer(offer_id: int) -> str:
    """Delete an offer and redirect back to the offers table."""

    offer = Offer.query.get_or_404(offer_id)
    db.session.delete(offer)
    db.session.commit()
    flash(f"Offer '{offer.title}' deleted successfully.", "success")
    return redirect(url_for("admin.dashboard_offers"))


@admin.route(
    "/offers/<int:offer_id>/notify", methods=["POST"], endpoint="trigger_offer_notification"
)
@admin_required
def trigger_offer_notification(offer_id: int) -> str:
    """Queue a broadcast notification for the specified offer."""

    offer = Offer.query.get_or_404(offer_id)
    broadcast_new_offer(offer.id)
    flash(f"Notification broadcast queued for '{offer.title}'.", "success")
    return redirect(url_for("admin.dashboard_offers"))
