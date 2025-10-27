"""Admin routes: communication center history, compose, detail, and lookup."""

from __future__ import annotations

from collections import deque
from datetime import datetime
from typing import Deque, Dict, Iterable, List, Optional, Sequence, Tuple

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
from sqlalchemy import or_

from app import db
from app.models import User, Company, Offer, ActivityLog
from app.services.roles import admin_required

from ...services import email_service
from ...services.notifications import send_admin_broadcast_notifications
from .. import admin

CommunicationLogEntry = Dict[str, object]

COMMUNICATION_HISTORY: Deque[CommunicationLogEntry] = deque(maxlen=200)

AUDIENCE_LABELS: Dict[str, str] = {
    "all_users": "جميع المستخدمين",
    "all_companies": "جميع الشركات",
    "all_employees": "جميع الموظفين",
    "selected_users": "مستخدمين محددين",
    "selected_companies": "شركات محددة",
}


def _ensure_admin_context() -> None:
    """Abort when the current request context lacks an administrative user."""

    user: Optional[User] = getattr(g, "current_user", None)
    if user is None:
        abort(403)
    if user.normalized_role not in {"admin", "superadmin"}:
        abort(403)


def _collect_company_members(companies: Iterable[Company]) -> List[User]:
    """Return a list of active users associated with the provided companies."""

    recipients: Dict[int, User] = {}
    for company in companies:
        if not company:
            continue
        owner = getattr(company, "owner", None)
        if owner and owner.is_active:
            recipients[owner.id] = owner
        company_users = getattr(company, "users", [])
        if hasattr(company_users, "all"):
            try:
                company_users = company_users.all()
            except Exception:  # pragma: no cover - dynamic loader guard
                company_users = []
        for user in company_users or []:
            if user and user.is_active:
                recipients[user.id] = user
    return list(recipients.values())


def _resolve_selected_users(raw_ids: Sequence[str]) -> List[User]:
    """Return active user models that match the provided identifier list."""

    user_ids = {int(item) for item in raw_ids if str(item).isdigit()}
    if not user_ids:
        return []
    return (
        User.query.filter(User.id.in_(user_ids), User.is_active.is_(True))
        .order_by(User.username)
        .all()
    )


def _resolve_selected_companies(raw_ids: Sequence[str]) -> List[Company]:
    """Return company models matching the provided identifier list."""

    company_ids = {int(item) for item in raw_ids if str(item).isdigit()}
    if not company_ids:
        return []
    return Company.query.filter(Company.id.in_(company_ids)).order_by(Company.name).all()


def _determine_recipients(
    audience: str,
    *,
    selected_users: Sequence[str] = (),
    selected_companies: Sequence[str] = (),
) -> Tuple[List[User], List[Company]]:
    """Return a tuple of (users, companies) matching the requested audience."""

    normalized = (audience or "all_users").strip().lower()

    if normalized == "all_users":
        users = (
            User.query.filter(User.is_active.is_(True))
            .order_by(User.username)
            .all()
        )
        return users, []

    if normalized == "all_companies":
        companies = Company.query.order_by(Company.name).all()
        company_users = _collect_company_members(companies)
        return company_users, companies

    if normalized == "all_employees":
        users = (
            User.query.filter(
                User.is_active.is_(True),
                User.role.in_(["admin", "superadmin"]),
            )
            .order_by(User.username)
            .all()
        )
        return users, []

    if normalized == "selected_users":
        users = _resolve_selected_users(selected_users)
        return users, []

    if normalized == "selected_companies":
        companies = _resolve_selected_companies(selected_companies)
        users = _collect_company_members(companies)
        return users, companies

    return [], []


def _format_recipient_snapshot(users: Sequence[User]) -> List[Dict[str, object]]:
    """Return serializable metadata describing selected user recipients."""

    snapshot: List[Dict[str, object]] = []
    for user in users:
        snapshot.append(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.normalized_role,
            }
        )
    return snapshot


def _log_communication(entry: CommunicationLogEntry) -> None:
    """Store a broadcast summary for administrative history rendering."""

    COMMUNICATION_HISTORY.appendleft(entry)


@admin.route("/communications")
@admin_required
def communication_history() -> str:
    """Render the administrative communication history ledger."""

    _ensure_admin_context()
    return render_template(
        "communications/index.html",
        section_title="Communication Center",
        active_page="communications",
        audience_labels=AUDIENCE_LABELS,
        history=list(COMMUNICATION_HISTORY),
    )


@admin.route("/communications/new", methods=["GET", "POST"])
@admin_required
def compose_communication() -> str:
    """Render the compose form and dispatch messages on submission."""

    _ensure_admin_context()

    if request.method == "POST":
        subject = (request.form.get("subject") or "").strip()
        body = (request.form.get("body") or "").strip()
        audience = (request.form.get("audience") or "all_users").strip().lower()
        send_via = request.form.getlist("send_via")
        selected_users = request.form.getlist("selected_users")
        selected_companies = request.form.getlist("selected_companies")

        if not subject:
            flash("يرجى إدخال عنوان للرسالة قبل الإرسال.", "danger")
            return redirect(url_for("admin.compose_communication"))

        if not body:
            flash("يرجى إدخال محتوى الرسالة قبل الإرسال.", "danger")
            return redirect(url_for("admin.compose_communication"))

        if not send_via:
            flash("اختر على الأقل وسيلة إرسال واحدة (بريد أو إشعار).", "danger")
            return redirect(url_for("admin.compose_communication"))

        user_recipients, company_scope = _determine_recipients(
            audience,
            selected_users=selected_users,
            selected_companies=selected_companies,
        )

        if not user_recipients:
            flash("لم يتم العثور على مستلمين مطابقين للمعايير المحددة.", "warning")
            return redirect(url_for("admin.compose_communication"))

        unique_user_ids = sorted({user.id for user in user_recipients})
        dispatch_results: Dict[str, object] = {
            "notifications": 0,
            "emails": 0,
        }

        sender: Optional[User] = getattr(g, "current_user", None)
        sender_id = getattr(sender, "id", None)

        if "notification" in send_via:
            dispatch_results["notifications"] = send_admin_broadcast_notifications(
                unique_user_ids,
                subject=subject,
                message=body,
                sent_by=sender_id,
            )

        if "email" in send_via:
            dispatch_results["emails"] = email_service.send_admin_broadcast_email(
                [user.email for user in user_recipients if user.email],
                subject=subject,
                sender=sender,
            )

        log_entry: CommunicationLogEntry = {
            "id": datetime.utcnow().strftime("%Y%m%d%H%M%S%f"),
            "subject": subject,
            "body": body,
            "audience": audience,
            "audience_label": AUDIENCE_LABELS.get(audience, audience),
            "send_via": list(send_via),
            "recipients": _format_recipient_snapshot(user_recipients),
            "companies": [
                {"id": company.id, "name": company.name}
                for company in company_scope
            ],
            "dispatched_at": datetime.utcnow(),
            "sent_by": getattr(sender, "username", "System"),
            "counts": dispatch_results,
        }
        _log_communication(log_entry)

        total_sent = (
            dispatch_results.get("notifications", 0)
            + dispatch_results.get("emails", 0)
        )
        flash(
            f"تم إرسال الرسالة بنجاح إلى {len(unique_user_ids)} مستلم (إجمالي العمليات: {total_sent}).",
            "success",
        )
        return redirect(url_for("admin.communication_history"))

    return render_template(
        "communications/compose.html",
        section_title="Compose Message",
        active_page="communications",
        audience_labels=AUDIENCE_LABELS,
    )


@admin.route("/communications/<string:entry_id>")
@admin_required
def communication_detail(entry_id: str) -> str:
    """Render a detailed view of a single communication record."""

    _ensure_admin_context()
    for entry in COMMUNICATION_HISTORY:
        if entry.get("id") == entry_id:
            return render_template(
                "communications/detail.html",
                section_title=entry.get("subject", "Communication"),
                active_page="communications",
                entry=entry,
            )
    abort(404)


@admin.route("/communications/lookup")
@admin_required
def communication_lookup() -> Response:
    """Return JSON payloads used for recipient autocomplete search widgets."""

    _ensure_admin_context()

    query_text = (request.args.get("query") or "").strip()
    lookup_type = (request.args.get("type") or "user").strip().lower()

    results: List[Dict[str, object]] = []

    if lookup_type == "company":
        base_query = Company.query
        if query_text:
            pattern = f"%{query_text}%"
            base_query = base_query.filter(Company.name.ilike(pattern))
        companies = base_query.order_by(Company.name).limit(20).all()
        for company in companies:
            results.append(
                {
                    "id": company.id,
                    "label": company.name,
                    "type": "company",
                }
            )
    else:
        base_query = User.query.filter(User.is_active.is_(True))
        if query_text:
            pattern = f"%{query_text}%"
            base_query = base_query.filter(
                or_(
                    User.username.ilike(pattern),
                    User.email.ilike(pattern),
                )
            )
        users = base_query.order_by(User.username).limit(20).all()
        for user in users:
            results.append(
                {
                    "id": user.id,
                    "label": f"{user.username} ({user.email})",
                    "type": "user",
                }
            )

    return jsonify({"results": results})
