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
        lazy="joined",
        post_update=True,
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


__all__ = ["Company"]
