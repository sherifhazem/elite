"""Offer redemption model providing single-use activation codes and QR tokens."""

from __future__ import annotations

from datetime import datetime, timedelta

from app.core.database import db


class Redemption(db.Model):
    """Represents a single-use redemption code generated for a user offer."""

    __tablename__ = "offer_redemptions"

    #: Maximum number of hours a redemption remains valid before expiring.
    EXPIRATION_HOURS = 48

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    offer_id = db.Column(db.Integer, db.ForeignKey("offers.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    redemption_code = db.Column(db.String(12), unique=True, nullable=False, index=True)
    qr_token = db.Column(db.String(36), unique=True, nullable=True)
    redeemed_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", back_populates="redemptions")
    offer = db.relationship("Offer", back_populates="redemptions")
    company = db.relationship("Company", back_populates="redemptions")

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        """Return a descriptive representation of the redemption."""

        return f"<Redemption {self.redemption_code} status={self.status}>"

    @property
    def expires_at(self) -> datetime | None:
        """Return the timestamp when the redemption code expires."""

        if self.created_at is None:
            return None
        return self.created_at + timedelta(hours=self.EXPIRATION_HOURS)

    def is_expired(self) -> bool:
        """Return True when the redemption has surpassed its validity window."""

        if self.status == "redeemed":
            return False
        expires_at = self.expires_at
        if expires_at is None:
            return False
        return datetime.utcnow() >= expires_at

    def mark_expired(self) -> None:
        """Mark the redemption as expired without committing the session."""

        self.status = "expired"

    def mark_redeemed(self) -> None:
        """Mark the redemption as redeemed and set the completion timestamp."""

        self.status = "redeemed"
        self.redeemed_at = datetime.utcnow()


__all__ = ["Redemption"]
