"""User model definition."""

from datetime import datetime

from app import db


class User(db.Model):
    """Represents an application user."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        """Return a string representation for debugging."""

        return f"<User {self.username}>"
