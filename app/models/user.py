"""User model definition."""

from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

from .. import db

from .. import db


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

    def set_password(self, password: str) -> None:
        """Hash and store the provided plain-text password."""

        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Validate a plain-text password against the stored hash."""

        return check_password_hash(self.password_hash, password)
