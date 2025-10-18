"""Notification model definition."""

from datetime import datetime

from .. import db


class Notification(db.Model):
    """Represents an in-app notification stored for a user."""

    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True, nullable=False)
    type = db.Column(db.String(40))
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link_url = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False, index=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True, nullable=False)
    metadata_json = db.Column(db.JSON)

    user = db.relationship("User", backref=db.backref("notifications", lazy="dynamic"))

    def __repr__(self) -> str:
        """Return string representation for debugging purposes."""

        return f"<Notification {self.type or 'general'} for user {self.user_id}>"
