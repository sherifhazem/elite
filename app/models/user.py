# LINKED: Fixed cascade deletion chain between Company → User → Notification
# Ensures safe automatic cleanup without manual deletion or integrity errors.
"""User model definition with role and permission helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.core.database import db

# Association table linking users to fine-grained permissions.
user_permissions = db.Table(
    "user_permissions",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column(
        "permission_id", db.Integer, db.ForeignKey("permissions.id"), primary_key=True
    ),
)


class User(UserMixin, db.Model):
    """Represents an application user with role-based access metadata.

    Key fields:
    - ``username`` and ``email``: Account identity fields.
    - ``role``: Authorization profile.

    Relationships:
    - ``company``: Linked company when the user is a business account.
    - ``notifications``: In-app notifications targeting the user.
    - ``permissions``: Optional fine-grained permissions.
    """

    __tablename__ = "users"

    #: List of supported roles ordered from least to most privileged.
    ROLE_CHOICES = ("member", "company", "admin", "superadmin")
    #: Mapping of required roles to the allowed role set, kept local to avoid cross-layer imports.
    ROLE_ACCESS_MATRIX = {
        "member": {"member", "company", "admin", "superadmin"},
        "company": {"company", "superadmin"},
        "admin": {"admin", "superadmin"},
        "superadmin": {"superadmin"},
    }

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    role = db.Column(
        db.String(50),
        default="member",
        nullable=False,
        doc="Application-wide role (member, company, admin, superadmin)",
    )
    phone_number = db.Column(
        db.String(20), 
        unique=True, 
        nullable=True,
        doc="Mobile phone number used for authentication and alerts."
    )
    is_phone_verified = db.Column(
        db.Boolean, 
        default=False,
        nullable=False,
        doc="Flag indicating if the phone number has been verified via OTP."
    )
    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
        doc="Flag indicating if the account is active and allowed to authenticate.",
    )
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=True,
        doc="Optional link to the company represented by the account.",
    )
    # FIX: specify foreign_keys to resolve AmbiguousForeignKeysError
    company = db.relationship(
        "Company",
        backref=db.backref(
            "users", lazy="dynamic", foreign_keys="User.company_id"
        ),
        lazy="joined",
        foreign_keys=[company_id],
        doc="Company entity associated with the user when acting as a business account.",
    )

    notifications = db.relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="dynamic",
        doc="In-app notifications associated with the user.",
    )

    #: Many-to-many relationship with Permission model for granular access checks.
    permissions = db.relationship(
        "Permission",
        secondary=user_permissions,
        lazy="dynamic",
        back_populates="users",
        doc="Optional fine-grained permissions granted in addition to the primary role.",
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

        normalized = (required_role or "member").strip().lower()
        allowed_roles = self.ROLE_ACCESS_MATRIX.get(normalized, {normalized})
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


__all__ = ["User", "user_permissions"]
