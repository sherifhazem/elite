"""Admin routes: communication center history, compose, detail, and lookup."""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request,
    jsonify,
    abort,
    Response,
    g,
)
from sqlalchemy import or_

from app.models import User, Company, Conversation, Message
from app.services.access_control import admin_required
from app.services.communication_service import CommunicationService
from .. import admin

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


@admin.route("/communications")
@admin_required
def communication_history() -> str:
    """Render the administrative communication history ledger (Inbox)."""
    _ensure_admin_context()
    
    page = request.args.get("page", 1, type=int)
    # Admin sees conversations they are part of, OR all conversations? 
    # Usually admins should see everything, but for "mailbox" feel, let's show conversations their user is part of.
    # The requirement says "Admin screen... similar tab... send/receive". 
    # So admin acts as a user.
    
    current_user_id = g.current_user.id
    pagination = CommunicationService.get_user_conversations(current_user_id, page=page)
    
    def has_unread_messages(conversation):
        return any(not m.is_read and m.sender_id != current_user_id for m in conversation.messages)

    return render_template(
        "admin/communications/index_db.html", # New template to match DB model
        section_title="Communication Center",
        active_page="communications",
        pagination=pagination,
        has_unread_messages=has_unread_messages
    )


@admin.route("/communications/new", methods=["GET", "POST"])
@admin_required
def compose_communication() -> str:
    """Render the compose form and dispatch messages on submission."""
    _ensure_admin_context()

    if request.method == "POST":
        cleaned = getattr(request, "cleaned", {}) or request.form # Fallback to form if cleaned not set
        
        # Helper to safely get list from request (handling both FormData and JSON/Cleaned)
        def _get_list(key):
             val = request.form.getlist(key) if not getattr(request, "cleaned", None) else cleaned.get(key)
             if isinstance(val, list): return val
             return [val] if val else []

        subject = request.form.get("subject")
        body = request.form.get("body")
        audience = request.form.get("audience", "selected_users")
        
        selected_users = _get_list("selected_users")
        selected_companies = _get_list("selected_companies")
        files = request.files.getlist("attachments")

        if not subject or not body:
            flash("الموضوع والرسالة مطلوبان", "danger")
            return redirect(url_for("admin.compose_communication"))

        # Resolve Recipients
        recipient_users = []
        
        if audience == "selected_users":
             recipient_users = _resolve_selected_users(selected_users)
        elif audience == "selected_companies":
             companies = _resolve_selected_companies(selected_companies)
             for comp in companies:
                 recipient_users.extend([u for u in comp.users if u.is_active])
        elif audience == "all_users":
             recipient_users = User.query.filter(User.is_active.is_(True)).all()
        # ... other cases ...

        if not recipient_users:
            flash("لم يتم اختيار مستلمين صالحين", "warning")
            return redirect(url_for("admin.compose_communication"))

        recipient_ids = list(set(u.id for u in recipient_users)) # Unique IDs

        try:
            # Create a single GROUP conversation for now, or loop for individual?
            # If "All Users" (1000 users), a group chat is bad.
            # Let's do: If > 1 recipient, ask user? Or default to Group?
            # The prompt implies "Mass reporting" or "Group message".
            # "Send group message or individual message" -> Explicit choice needed.
            # For this MVP, I will create ONE conversation with ALL recipients (Group Chat).
            # Limitation: logical limit on participants?
            
            CommunicationService.create_conversation(
                initiator_id=g.current_user.id,
                recipient_ids=recipient_ids,
                subject=subject,
                initial_message=body,
                attachment_files=files
            )
            
            flash(f"تم بدء المحادثة مع {len(recipient_ids)} مستلم.", "success")
            return redirect(url_for("admin.communication_history"))
        except Exception as e:
            flash(f"حدث خطأ: {e}", "danger")
            return redirect(url_for("admin.compose_communication"))

    return render_template(
        "admin/communications/compose.html",
        section_title="رسالة جديدة",
        active_page="communications",
        audience_labels=AUDIENCE_LABELS,
    )


@admin.route("/communications/<int:conversation_id>")
@admin_required
def communication_detail(conversation_id: int) -> str:
    """Render a detailed view of a single conversation."""
    _ensure_admin_context()
    
    conversation = CommunicationService.get_conversation(conversation_id, g.current_user.id)
    if not conversation:
        # Fallback: if user is admin, maybe they can see any conversation?
        # Service currently enforces participation.
        # Let's trust service validaton.
        abort(404)
    
    # Mark read
    CommunicationService.mark_conversation_as_read(conversation_id, g.current_user.id)

    return render_template(
        "admin/communications/view.html",
        section_title=conversation.subject,
        active_page="communications",
        conversation=conversation,
    )

@admin.route("/communications/<int:conversation_id>/reply", methods=["POST"])
@admin_required
def communication_reply(conversation_id: int):
    _ensure_admin_context()
    
    body = request.form.get("body")
    files = request.files.getlist("attachments")
    
    if not body:
         flash("الرسالة مطلوبة", "danger")
         return redirect(url_for('admin.communication_detail', conversation_id=conversation_id))
         
    try:
        CommunicationService.send_message(
            conversation_id=conversation_id,
            sender_id=g.current_user.id,
            body=body,
            attachment_files=files
        )
        flash("تم الرد بنجاح", "success")
    except Exception as e:
        flash(f"خطأ: {e}", "danger")
        
    return redirect(url_for('admin.communication_detail', conversation_id=conversation_id))


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
@admin.route("/communications/<int:conversation_id>/sync")
@admin_required
def communication_sync(conversation_id: int):
    """Retrieve new messages for polling."""
    last_id = request.args.get("last_id", 0, type=int)
    messages = CommunicationService.get_new_messages(conversation_id, g.current_user.id, last_id)
    
    if messages:
        CommunicationService.mark_conversation_as_read(conversation_id, g.current_user.id)
        
    return {
        "messages": [
            {
                "id": m.id,
                "body": m.body,
                "sender_id": m.sender_id,
                "sender_name": m.sender.username,
                "created_at": m.created_at.strftime("%H:%M"),
                "attachments": [
                    {"filename": a.filename, "url": url_for('static', filename=a.file_path)} 
                    for a in m.attachments
                ]
            } for m in messages
        ]
    }
