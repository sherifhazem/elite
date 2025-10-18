"""User model definition."""

from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

from .. import db



class User(db.Model):
    """Represents an application user."""

    __tablename__ = "users"

    #: Tuple defining the allowed membership levels in ascending order.
    MEMBERSHIP_LEVELS = ("Basic", "Silver", "Gold", "Premium")

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
        doc="Flag indicating if the user can access the admin dashboard.",
    )
    membership_level = db.Column(
        db.String(50),
        default="Basic",
        nullable=False,
        doc="Tracks the membership tier assigned to the user.",
    )
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

    @classmethod
    def normalize_membership_level(cls, level: str) -> str:
        """Return a normalized membership level when valid, otherwise an empty string."""

        if not level or not isinstance(level, str):
            return ""
        normalized = level.strip().title()
        if normalized in cls.MEMBERSHIP_LEVELS:
            return normalized
        return ""

    def update_membership_level(self, level: str) -> None:
        """Update the user's membership level for tier-based access control."""

        normalized = self.normalize_membership_level(level)
        if not normalized:
            raise ValueError("Membership level must be one of: Basic, Silver, Gold, Premium.")
        self.membership_level = normalized

    def membership_rank(self) -> int:
        """Return the index of the current membership level for comparison operations."""

        normalized = self.normalize_membership_level(self.membership_level or "Basic")
        try:
            return self.MEMBERSHIP_LEVELS.index(normalized or "Basic")
        except ValueError:
            return 0

    def can_upgrade_to(self, new_level: str) -> bool:
        """Return True when the provided level is higher than the current membership."""

        normalized = self.normalize_membership_level(new_level)
        if not normalized:
            return False
        try:
            desired_rank = self.MEMBERSHIP_LEVELS.index(normalized)
        except ValueError:
            return False
        return desired_rank > self.membership_rank()
