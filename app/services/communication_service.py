"""Service for handling internal communications."""

import os
import uuid
from datetime import datetime
from typing import List, Optional

from werkzeug.utils import secure_filename
from flask import current_app

from app.core.database import db
from app.models import User, Conversation, Message, Attachment

class CommunicationService:
    """Service class for managing conversations and messages."""

    @staticmethod
    def create_conversation(initiator_id: int, recipient_ids: List[int], subject: str, initial_message: str, attachment_files: List = None) -> Conversation:
        """Create a new conversation with an initial message."""
        try:
            initiator = User.query.get(initiator_id)
            if not initiator:
                raise ValueError("Initiator not found")

            # Create conversation
            conversation = Conversation(
                subject=subject,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            conversation.participants.append(initiator)
            
            for recipient_id in recipient_ids:
                recipient = User.query.get(recipient_id)
                if recipient:
                    conversation.participants.append(recipient)
            
            db.session.add(conversation)
            db.session.flush() # flush to get conversation ID

            # Add initial message
            CommunicationService.send_message(
                conversation_id=conversation.id,
                sender_id=initiator_id,
                body=initial_message,
                attachment_files=attachment_files
            )

            db.session.commit()
            return conversation
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def send_message(conversation_id: int, sender_id: int, body: str, attachment_files: List = None) -> Message:
        """Send a message to an existing conversation."""
        conversation = Conversation.query.get(conversation_id)
        if not conversation:
            raise ValueError("Conversation not found")

        message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            body=body,
            created_at=datetime.utcnow()
        )
        db.session.add(message)
        db.session.flush()

        # Handle attachments
        if attachment_files:
            upload_folder = os.path.join(current_app.static_folder, 'uploads', 'attachments')
            os.makedirs(upload_folder, exist_ok=True)

            for file_storage in attachment_files:
                if file_storage and file_storage.filename:
                    filename = secure_filename(file_storage.filename)
                    # Generate unique filename
                    unique_name = f"{uuid.uuid4().hex}_{filename}"
                    file_path = os.path.join(upload_folder, unique_name)
                    relative_path = f"uploads/attachments/{unique_name}"
                    
                    file_storage.save(file_path)
                    
                    attachment = Attachment(
                        message_id=message.id,
                        filename=filename,
                        file_path=relative_path,
                        file_type=file_storage.content_type,
                        # file_size could be added if needed
                    )
                    db.session.add(attachment)

        # Update conversation updated_at
        conversation.updated_at = datetime.utcnow()
        
        # --- Create Notifications for participants ---
        from app.models import Notification
        sender = User.query.get(sender_id)
        sender_name = sender.username if sender else "مستخدم"
        
        for participant in conversation.participants:
            if participant.id != sender_id:
                # Determine portal link
                portal_link = f"/portal/messages/{conversation.id}" # default
                role = participant.normalized_role
                if role in ["admin", "superadmin"]:
                    portal_link = f"/admin/communications/{conversation.id}"
                elif role == "company":
                    portal_link = f"/company/messages/{conversation.id}"

                notif = Notification(
                    user_id=participant.id,
                    type="message",
                    title="رسالة جديدة",
                    message=f"لديك رسالة جديدة من {sender_name}: {body[:50]}...",
                    link_url=portal_link,
                    is_read=False,
                    created_at=datetime.utcnow()
                )
                db.session.add(notif)
        
        db.session.commit()
        return message

    @staticmethod
    def get_new_messages(conversation_id: int, user_id: int, last_message_id: int) -> List[Message]:
        """Get messages in a conversation created after a specific ID."""
        conversation = CommunicationService.get_conversation(conversation_id, user_id)
        if not conversation:
            return []
        
        return conversation.messages.filter(Message.id > last_message_id).all()

    @staticmethod
    def get_user_conversations(user_id: int, page: int = 1, per_page: int = 20):
        """Get conversations for a user, ordered by most recently updated."""
        user = User.query.get(user_id)
        if not user:
            return []
            
        return Conversation.query.join(Conversation.participants)\
            .filter(User.id == user_id)\
            .order_by(Conversation.updated_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_conversation(conversation_id: int, user_id: int) -> Optional[Conversation]:
        """Get a single conversation if the user is a participant."""
        conversation = Conversation.query.get(conversation_id)
        if not conversation:
            return None
            
        # Check participation
        participant_ids = [u.id for u in conversation.participants]
        if user_id not in participant_ids:
            # Check if user is admin (admins might see all?) 
            # For now strict participation check, assuming admin adds themselves or has override
            user = User.query.get(user_id)
            if not (user and user.is_superadmin): # Superadmin override
                return None
        
        return conversation

    @staticmethod
    def mark_conversation_as_read(conversation_id: int, user_id: int):
        """Mark all messages in a conversation as read for a specific user (logic might vary)."""
        # In this simple model, read_at is on the message. 
        # So we mark all messages NOT sent by the user as read.
        messages = Message.query.filter(
            Message.conversation_id == conversation_id,
            Message.sender_id != user_id,
            Message.read_at.is_(None)
        ).all()
        
        for msg in messages:
            msg.read_at = datetime.utcnow()
            
        db.session.commit()

    @staticmethod
    def get_unread_count(user_id: int) -> int:
        """Count total unread messages for a user across all conversations."""
        # This query is a bit complex: Count messages where user is a participant of the conversation
        # AND message sender is NOT the user AND message is unread.
        
        # 1. Get user conversations
        user_conversations = db.session.query(Conversation.id).join(
            Conversation.participants
        ).filter(User.id == user_id).subquery()
        
        # 2. Count unread messages in those conversations
        count = Message.query.filter(
            Message.conversation_id.in_(user_conversations),
            Message.sender_id != user_id,
            Message.read_at.is_(None)
        ).count()
        
        return count
