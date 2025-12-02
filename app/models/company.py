"""Company model representing a business collaborating with ELITE.

Key fields:
- ``name``: Company name.
- ``status``: Moderation state such as ``pending``.
- ``notification_preferences``: Mutable JSON storing contact preferences.

Relationships:
- ``owner``: The primary user who owns the company account.
- ``redemptions``: Offer redemptions associated with the company.
"""

from datetime import datetime

from sqlalchemy.ext.mutable import MutableDict

from app.core.database import db


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
    status = db.Column(db.String(20), default="pending", nullable=False)
    admin_notes = db.Column(db.Text, nullable=True)

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
        """Return a concise representation for debugging."""

        return f"<Company {self.name}>"


__all__ = ["Company"]
