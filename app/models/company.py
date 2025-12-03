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


def _safe_preferences(company: "Company") -> MutableDict:
    """Return a mutable dictionary for notification preferences."""

    prefs = company.notification_preferences or {}
    if not isinstance(prefs, MutableDict):
        prefs = MutableDict(prefs if isinstance(prefs, dict) else {})
        company.notification_preferences = prefs
    return prefs


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

    # Convenience properties pulled from notification preferences/owner
    @property
    def contact_number(self) -> str | None:
        prefs = _safe_preferences(self)
        return (
            prefs.get("contact_phone")
            or prefs.get("phone")
            or prefs.get("contact_number")
        )

    @contact_number.setter
    def contact_number(self, value: str | None) -> None:
        prefs = _safe_preferences(self)
        prefs["contact_phone"] = value or None

    @property
    def city(self) -> str | None:
        prefs = _safe_preferences(self)
        return prefs.get("city")

    @city.setter
    def city(self, value: str | None) -> None:
        prefs = _safe_preferences(self)
        prefs["city"] = value or None

    @property
    def industry(self) -> str | None:
        prefs = _safe_preferences(self)
        return prefs.get("industry")

    @industry.setter
    def industry(self, value: str | None) -> None:
        prefs = _safe_preferences(self)
        prefs["industry"] = value or None

    @property
    def website_url(self) -> str | None:
        prefs = _safe_preferences(self)
        return prefs.get("website_url")

    @website_url.setter
    def website_url(self, value: str | None) -> None:
        prefs = _safe_preferences(self)
        prefs["website_url"] = value or None

    @property
    def social_url(self) -> str | None:
        prefs = _safe_preferences(self)
        return prefs.get("social_url")

    @social_url.setter
    def social_url(self, value: str | None) -> None:
        prefs = _safe_preferences(self)
        prefs["social_url"] = value or None

    @property
    def email(self) -> str | None:
        prefs = _safe_preferences(self)
        return prefs.get("contact_email") or getattr(self.owner, "email", None)

    @email.setter
    def email(self, value: str | None) -> None:
        prefs = _safe_preferences(self)
        prefs["contact_email"] = value or None
        if self.owner:
            self.owner.email = value or self.owner.email

    def __repr__(self) -> str:
        """Return a concise representation for debugging."""

        return f"<Company {self.name}>"


__all__ = ["Company"]
