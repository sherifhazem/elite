"""Communication routes for the company portal."""

from flask import render_template, request, flash, redirect, url_for, g

from app.modules.companies import company_portal
from app.services.communication_service import CommunicationService
from app.models import User
from app.services.access_control import company_required
from app.modules.companies.routes.permissions import guard_company_staff_only_tabs

@company_portal.route("/messages")
@company_required
def company_messages_list():
    """Display list of conversations for the current company user."""
    permission_guard = guard_company_staff_only_tabs()
    if permission_guard is not None:
        return permission_guard
    current_user = g.current_user
    page = request.args.get("page", 1, type=int)
    pagination = CommunicationService.get_user_conversations(current_user.id, page=page)
    
    def has_unread_messages(conversation):
        # Helper to check for unread messages from other participants
        return any(not m.is_read and m.sender_id != current_user.id for m in conversation.messages)

    return render_template("communications/list.html", pagination=pagination, has_unread_messages=has_unread_messages)

@company_portal.route("/messages/new", methods=["GET", "POST"])
@company_required
def company_messages_new():
    """Create a new conversation (Send message to Admin)."""
    permission_guard = guard_company_staff_only_tabs()
    if permission_guard is not None:
        return permission_guard
    current_user = g.current_user
    if request.method == "POST":
        subject = request.form.get("subject")
        body = request.form.get("body")
        files = request.files.getlist("attachments")
        
        if not subject or not body:
            flash("الموضوع والرسالة مطلوبان", "danger")
            return redirect(url_for("company_portal.company_messages_new"))

        # Find Admin users to receive the message
        # For simplicity, sending to all admins or a specific support admin
        # Using a helper or query to find admins
        admins = User.query.filter(User.role.in_(['admin', 'superadmin'])).all()
        active_admins = [u.id for u in admins if u.is_active]

        if not active_admins:
             flash("لا يوجد مسؤولين متاحين حاليا.", "warning")
             return redirect(url_for("company_portal.company_messages_new"))
        
        try:
            CommunicationService.create_conversation(
                initiator_id=current_user.id,
                recipient_ids=active_admins,
                subject=subject,
                initial_message=body,
                attachment_files=files
            )
            flash("تم ارسال الرسالة بنجاح", "success")
            return redirect(url_for("company_portal.company_messages_list"))
        except Exception as e:
            flash(f"حدث خطأ أثناء الإرسال: {str(e)}", "danger")

    return render_template("communications/compose.html")

@company_portal.route("/messages/<int:conversation_id>")
@company_required
def company_messages_view(conversation_id):
    """View a single conversation."""
    permission_guard = guard_company_staff_only_tabs()
    if permission_guard is not None:
        return permission_guard
    current_user = g.current_user
    conversation = CommunicationService.get_conversation(conversation_id, current_user.id)
    if not conversation:
        flash("المحادثة غير موجودة أو ليس لديك صلاحية الوصول إليها", "danger")
        return redirect(url_for("company_portal.company_messages_list"))
    
    # Mark as read logic could be here or on specific action
    CommunicationService.mark_conversation_as_read(conversation.id, current_user.id)

    return render_template("communications/view.html", conversation=conversation)

@company_portal.route("/messages/<int:conversation_id>/reply", methods=["POST"])
@company_required
def company_messages_reply(conversation_id):
    """Reply to an existing conversation."""
    permission_guard = guard_company_staff_only_tabs()
    if permission_guard is not None:
        return permission_guard
    current_user = g.current_user
    body = request.form.get("body")
    files = request.files.getlist("attachments")
    
    if not body:
        flash("الرسالة فارغة", "danger")
        return redirect(url_for("company_portal.company_messages_view", conversation_id=conversation_id))

    try:
        CommunicationService.send_message(
            conversation_id=conversation_id,
            sender_id=current_user.id,
            body=body,
            attachment_files=files
        )
        flash("تم الرد بنجاح", "success")
    except Exception as e:
        flash(f"حدث خطأ أثناء الرد: {str(e)}", "danger")
        
    return redirect(url_for("company_portal.company_messages_view", conversation_id=conversation_id))


@company_portal.route("/messages/<int:conversation_id>/sync")
@company_required
def company_messages_sync(conversation_id):
    """Retrieve new messages for polling."""
    permission_guard = guard_company_staff_only_tabs()
    if permission_guard is not None:
        return permission_guard
    current_user = g.current_user
    last_id = request.args.get("last_id", 0, type=int)
    messages = CommunicationService.get_new_messages(conversation_id, current_user.id, last_id)
    
    # Mark as read if user is syncing
    if messages:
        CommunicationService.mark_conversation_as_read(conversation_id, current_user.id)
        
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


@company_portal.route("/api/messages/unread-count")
@company_required
def get_company_unread_count():
    """Endpoint for global unread message count badge."""
    permission_guard = guard_company_staff_only_tabs()
    if permission_guard is not None:
        return permission_guard
    count = CommunicationService.get_unread_count(g.current_user.id)
    return {"unread_count": count}
