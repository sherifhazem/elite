"""Communication routes for the member portal."""

from flask import render_template, request, flash, redirect, url_for, g
from app.modules.members.routes.user_portal_routes import portal, _resolve_user_context, _redirect_to_login
from app.services.communication_service import CommunicationService
from app.models import User

@portal.route("/messages", endpoint="member_messages_list")
def member_messages_list():
    """Display list of conversations for the current member."""
    user = _resolve_user_context()
    if user is None:
        return _redirect_to_login()
        
    page = request.args.get("page", 1, type=int)
    pagination = CommunicationService.get_user_conversations(user.id, page=page)
    
    def has_unread_messages(conversation):
        return any(not m.is_read and m.sender_id != user.id for m in conversation.messages)
        
    return render_template(
        "members/portal/communications/list.html",
        user=user,
        pagination=pagination,
        has_unread_messages=has_unread_messages,
        active_nav="messages"
    )

@portal.route("/messages/new", methods=["GET", "POST"], endpoint="member_messages_new")
def member_messages_new():
    """Create a new conversation with Admin."""
    user = _resolve_user_context()
    if user is None:
        return _redirect_to_login()

    if request.method == "POST":
        subject = request.form.get("subject")
        body = request.form.get("body")
        files = request.files.getlist("attachments")
        
        if not subject or not body:
            flash("الموضوع والرسالة مطلوبان", "danger")
            return redirect(url_for("portal.member_messages_new"))

        # Send to valid admins
        admins = User.query.filter(User.role.in_(['admin', 'superadmin']), User.is_active.is_(True)).all()
        admin_ids = [u.id for u in admins]
        
        if not admin_ids:
             flash("لا يوجد مسؤولين للمراسلة", "warning")
             return redirect(url_for("portal.member_messages_new"))

        try:
            CommunicationService.create_conversation(
                initiator_id=user.id,
                recipient_ids=admin_ids, # Send to all admins? Or one conversation with all admins?
                subject=subject,
                initial_message=body,
                attachment_files=files
            )
            flash("تم ارسال الرسالة بنجاح", "success")
            return redirect(url_for("portal.member_messages_list"))
        except Exception as e:
            flash(f"خطأ: {str(e)}", "danger")

    return render_template(
        "members/portal/communications/compose.html",
        user=user,
        active_nav="messages"
    )

@portal.route("/messages/<int:conversation_id>", endpoint="member_messages_view")
def member_messages_view(conversation_id):
    """View conversation."""
    user = _resolve_user_context()
    if user is None:
        return _redirect_to_login()
        
    conversation = CommunicationService.get_conversation(conversation_id, user.id)
    if not conversation:
        flash("المحادثة غير موجودة", "danger")
        return redirect(url_for("portal.member_messages_list"))
    
    CommunicationService.mark_conversation_as_read(conversation.id, user.id)
    
    return render_template(
        "members/portal/communications/view.html",
        user=user,
        conversation=conversation,
        active_nav="messages"
    )

@portal.route("/messages/<int:conversation_id>/reply", methods=["POST"], endpoint="member_messages_reply")
def member_messages_reply(conversation_id):
    """Reply to conversation."""
    user = _resolve_user_context()
    if user is None:
        return _redirect_to_login()
        
    body = request.form.get("body")
    files = request.files.getlist("attachments")
    
    if body:
        try:
            CommunicationService.send_message(
                conversation_id=conversation_id,
                sender_id=user.id,
                body=body,
                attachment_files=files
            )
            flash("تم الرد", "success")
        except Exception as e:
            flash(f"خطأ: {e}", "danger")
            
    return redirect(url_for("portal.member_messages_view", conversation_id=conversation_id))
@portal.route("/messages/<int:conversation_id>/sync", endpoint="member_messages_sync")
def member_messages_sync(conversation_id):
    """Retrieve new messages for polling."""
    user = _resolve_user_context()
    if user is None:
        return {"error": "Unauthorized"}, 401
        
    last_id = request.args.get("last_id", 0, type=int)
    messages = CommunicationService.get_new_messages(conversation_id, user.id, last_id)
    
    if messages:
        CommunicationService.mark_conversation_as_read(conversation_id, user.id)
        
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
