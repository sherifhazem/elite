"""Admin routes: reporting dashboards, summaries, and exports."""

from __future__ import annotations

from io import BytesIO
from typing import Any, Dict

from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request,
    jsonify,
    abort,
    Response,
    send_file,
)

from app import db
from app.models import User, Company, Offer, ActivityLog
from app.services.access_control import admin_required

from app.modules.admin.services.analytics import (
    get_company_summary,
    get_membership_distribution,
    get_offer_summary,
    get_recent_activity,
    get_user_summary,
)
from .. import admin


@admin.route("/reports", endpoint="reports_home")
@admin_required
def reports_home() -> str:
    """Render the interactive reports dashboard."""

    return render_template(
        "dashboard/reports.html",
        section_title="التقارير والتحليلات",
    )


@admin.route("/api/summary", endpoint="summary_api")
@admin_required
def summary_api() -> Any:
    """Return a JSON payload with aggregated platform statistics."""

    user_summary = get_user_summary()
    offer_summary = get_offer_summary()

    payload: Dict[str, Any] = {
        "users": user_summary,
        "companies": get_company_summary(),
        "offers": offer_summary,
        "membership_distribution": get_membership_distribution(),
        "recent_activity": get_recent_activity(),
        "recent_offers": offer_summary["latest"],
    }
    return jsonify(payload)


@admin.route("/reports/export", endpoint="export_pdf")
@admin_required
def export_pdf() -> Any:
    """Generate a PDF report for download using the latest analytics."""

    offer_summary = get_offer_summary()
    payload: Dict[str, Any] = {
        "users": get_user_summary(),
        "companies": get_company_summary(),
        "offers": offer_summary,
        "recent_offers": offer_summary["latest"],
    }

    buffer = BytesIO()
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ModuleNotFoundError:
        return (
            jsonify(
                {
                    "error": "reportlab dependency is not installed.",
                    "message": "Install reportlab to enable PDF exports.",
                }
            ),
            501,
        )

    pdf = canvas.Canvas(buffer, pagesize=A4)
    _, height = A4

    pdf.setTitle("ELITE Admin Report")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(40, height - 60, "ELITE Performance Snapshot")

    pdf.setFont("Helvetica", 12)
    y = height - 100

    users = payload.get("users", {})
    pdf.drawString(40, y, f"Total Users: {users.get('total_users', 0)}")
    y -= 20
    pdf.drawString(40, y, f"New (7d): {users.get('new_last_7_days', 0)}")

    companies = payload.get("companies", {})
    y -= 30
    pdf.drawString(40, y, f"Total Companies: {companies.get('total_companies', 0)}")

    offers = payload.get("offers", {})
    y -= 30
    pdf.drawString(40, y, f"Active Offers: {offers.get('active_offers', 0)}")
    y -= 20
    pdf.drawString(40, y, f"Average Discount: {offers.get('average_discount', 0)}%")

    y -= 40
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(40, y, "Latest Offers")
    pdf.setFont("Helvetica", 11)
    y -= 20
    for offer in payload.get("recent_offers", [])[:5]:
        title = offer.get("title", "")
        company = offer.get("company", "-")
        created_at = offer.get("created_at", "")
        pdf.drawString(45, y, f"• {title} ({company}) – {created_at}")
        y -= 16
        if y < 80:
            pdf.showPage()
            y = height - 80
            pdf.setFont("Helvetica", 11)

    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="elite-reports.pdf",
    )
