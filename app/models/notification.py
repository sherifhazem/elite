# LINKED: Fixed cascade deletion chain between Company → User → Notification
# Ensures safe automatic cleanup without manual deletion or integrity errors.
"""Notification model definition."""

from datetime import datetime

from app.core.database import db


class Notification(db.Model):
    """Represents an in-app notification stored for a user."""

    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    type = db.Column(db.String(40))
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link_url = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False, index=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True, nullable=False)
    metadata_json = db.Column(db.JSON)

    user = db.relationship("User", back_populates="notifications")

    def __repr__(self) -> str:
        """Return string representation for debugging purposes."""

        return f"<Notification {self.type or 'general'} for user {self.user_id}>"
