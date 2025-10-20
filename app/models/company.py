# LINKED: Fixed cascade deletion chain between Company → User → Notification
# Ensures safe automatic cleanup without manual deletion or integrity errors.
"""Company model definition with ownership and branding metadata."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from sqlalchemy.ext.mutable import MutableDict

from .. import db


class Company(db.Model):
    """Represents a company collaborating with ELITE."""

    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    owner_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    logo_url = db.Column(db.String(255), nullable=True)
    notification_preferences = db.Column(
        MutableDict.as_mutable(db.JSON), default=dict, nullable=False
    )

    owner = db.relationship(
        "User",
        foreign_keys=[owner_user_id],
        backref=db.backref("owned_companies", lazy="dynamic"),
        cascade="all, delete-orphan",
        lazy="joined",
        passive_deletes=True,
        post_update=True,
        single_parent=True,
        uselist=False,
    )

    redemptions = db.relationship(
        "Redemption",
        back_populates="company",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Return a string representation for debugging."""

        return f"<Company {self.name}>"

    def notification_settings(self) -> Dict[str, Any]:
        """Return notification preferences while ensuring a dictionary output."""

        preferences = self.notification_preferences or {}
        if not isinstance(preferences, dict):
            return {}
        return preferences

    def remove_owner_account(self) -> None:
        """Delete the owner account while leaving member accounts untouched."""

        from .user import User

        owners = []
        if self.owner is not None:
            owners.append(self.owner)

        owners.extend(
            User.query.filter(
                User.company_id == self.id,
                User.role == "company",
            ).all()
        )

        seen_ids = set()
        for owner in owners:
            if owner and owner.id not in seen_ids:
                seen_ids.add(owner.id)
                db.session.delete(owner)


__all__ = ["Company"]
