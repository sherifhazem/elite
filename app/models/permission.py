"""Permission model enabling fine-grained access rules."""

from __future__ import annotations

from app.core.database import db


class Permission(db.Model):
    """Represents a named permission that can be assigned to users.

    Relationships:
    - ``users``: Accounts that reference the permission through
      ``user_permissions`` association table.
    """

    __tablename__ = "permissions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.String(255))

    users = db.relationship(
        "User",
        secondary="user_permissions",
        lazy="dynamic",
        back_populates="permissions",
        doc="Users granted this permission in addition to their primary role.",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        """Return the permission name for easier debugging."""

        return f"<Permission {self.name}>"


__all__ = ["Permission"]
