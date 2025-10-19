"""User model definition with role and permission helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from werkzeug.security import check_password_hash, generate_password_hash

from .. import db

# Association table linking users to fine-grained permissions.
user_permissions = db.Table(
    "user_permissions",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column(
        "permission_id", db.Integer, db.ForeignKey("permissions.id"), primary_key=True
    ),
)


class User(db.Model):
    """Represents an application user with role-based access metadata."""

    __tablename__ = "users"

    #: Tuple defining the allowed membership levels in ascending order.
    MEMBERSHIP_LEVELS = ("Basic", "Silver", "Gold", "Premium")

    #: List of supported roles ordered from least to most privileged.
    ROLE_CHOICES = ("member", "company", "admin", "superadmin")

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(
        db.String(50),
        default="member",
        nullable=False,
        doc="Application-wide role (member, company, admin, superadmin)",
    )
    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
        doc="Flag indicating if the account is active and allowed to authenticate.",
    )
    membership_level = db.Column(
        db.String(50),
        default="Basic",
        nullable=False,
        doc="Tracks the membership tier assigned to the user.",
    )
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=True,
        doc="Optional link to the company represented by the account.",
    )
    company = db.relationship(
        "Company",
        backref=db.backref("users", lazy="dynamic"),
        lazy="joined",
        doc="Company entity associated with the user when acting as a business account.",
    )

    #: Many-to-many relationship with Permission model for granular access checks.
    permissions = db.relationship(
        "Permission",
        secondary=user_permissions,
        lazy="dynamic",
        back_populates="users",
        doc="Optional fine-grained permissions granted in addition to the primary role.",
    )

    redemptions = db.relationship(
        "Redemption",
        back_populates="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
        doc="Offer redemption activations created by the member.",
    )

    # ------------------------------------------------------------------
    # Representations & authentication helpers
    # ------------------------------------------------------------------
    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        """Return a string representation for debugging."""

        return f"<User {self.username} ({self.role})>"

    def set_password(self, password: str) -> None:
        """Hash and store the provided plain-text password."""

        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Validate a plain-text password against the stored hash."""

        return check_password_hash(self.password_hash, password)

    # ------------------------------------------------------------------
    # Role helpers
    # ------------------------------------------------------------------
    @property
    def normalized_role(self) -> str:
        """Return the normalized role string or a safe default."""

        role = (self.role or "member").strip().lower()
        if role not in self.ROLE_CHOICES:
            return "member"
        return role

    @property
    def is_admin(self) -> bool:
        """Compatibility helper indicating if the user has administrative privileges."""

        return self.normalized_role in {"admin", "superadmin"}

    @property
    def is_superadmin(self) -> bool:
        """Return True when the account has super administrator privileges."""

        return self.normalized_role == "superadmin"

    def set_role(self, role: str) -> None:
        """Validate and store a new role for the user."""

        normalized = (role or "").strip().lower()
        if normalized not in self.ROLE_CHOICES:
            allowed = ", ".join(self.ROLE_CHOICES)
            raise ValueError(f"Role must be one of: {allowed}.")
        self.role = normalized

    def has_role(self, required_role: str) -> bool:
        """Return True when the user matches the required role constraint."""

        from ..services.roles import ROLE_ACCESS_MATRIX

        normalized = (required_role or "member").strip().lower()
        allowed_roles = ROLE_ACCESS_MATRIX.get(normalized, {normalized})
        return self.normalized_role in allowed_roles

    def grant_permissions(self, permission_names: Iterable[str]) -> None:
        """Assign multiple permissions to the user if available."""

        from .permission import Permission

        if not permission_names:
            return

        normalized_names = {name.strip().lower() for name in permission_names if name}
        if not normalized_names:
            return

        existing_permissions = {
            perm.name.lower(): perm
            for perm in Permission.query.filter(Permission.name.in_(normalized_names)).all()
        }
        for name in normalized_names:
            permission = existing_permissions.get(name)
            if permission and permission not in self.permissions:
                self.permissions.append(permission)

    # ------------------------------------------------------------------
    # Membership helpers
    # ------------------------------------------------------------------
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


__all__ = ["User", "user_permissions"]
