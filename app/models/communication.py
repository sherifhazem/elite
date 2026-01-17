"""Communication models: Conversation, Message, and Attachment."""

from datetime import datetime

from app.core.database import db

# Association table for conversation participants
conversation_participants = db.Table(
    "conversation_participants",
    db.Column("conversation_id", db.Integer, db.ForeignKey("conversations.id"), primary_key=True),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
)


class Conversation(db.Model):
    """Represents a thread of messages between users."""

    __tablename__ = "conversations"

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    participants = db.relationship(
        "User",
        secondary=conversation_participants,
        lazy="dynamic",
        backref=db.backref("conversations", lazy="dynamic"),
    )
    
    messages = db.relationship(
        "Message",
        backref="conversation",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )

    @property
    def last_message(self):
        """Return the most recent message in the thread."""
        return self.messages.order_by(Message.created_at.desc()).first()

    def __repr__(self) -> str:
        return f"<Conversation {self.id} - {self.subject}>"


class Message(db.Model):
    """Represents an individual message within a conversation."""

    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id"), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    read_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    sender = db.relationship("User", backref="sent_messages")
    
    attachments = db.relationship(
        "Attachment",
        backref="message",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )

    @property
    def is_read(self) -> bool:
        return self.read_at is not None

    def __repr__(self) -> str:
        return f"<Message {self.id} from {self.sender_id}>"


class Attachment(db.Model):
    """Represents a file attached to a message."""

    __tablename__ = "attachments"

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey("messages.id"), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    file_type = db.Column(db.String(100), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)  # Size in bytes
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Attachment {self.filename} ({self.id})>"
