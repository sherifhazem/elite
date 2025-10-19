"""Offer model definition."""

from datetime import datetime

from .. import db


class Offer(db.Model):
    """Represents an offer provided by a company."""

    __tablename__ = "offers"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    # Store the minimum discount value that all users can access.
    base_discount = db.Column(db.Float, nullable=False, default=5.0)
    valid_until = db.Column(db.DateTime, nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Establish relationship with Company for easy access to related offers
    company = db.relationship("Company", backref="offers")

    redemptions = db.relationship(
        "Redemption",
        back_populates="offer",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Return a string representation for debugging."""

        return f"<Offer {self.title} - base {self.base_discount}%>"

    def get_discount_for_level(self, level: str) -> float:
        """Return discount value based on membership level."""

        # Normalize the incoming level to simplify comparisons.
        normalized = (level or "").strip().lower()
        # Map membership tiers to the amount added on top of the base discount.
        adjustments = {
            "basic": 0.0,
            "silver": 5.0,
            "gold": 10.0,
            "premium": 15.0,
        }
        # Retrieve the adjustment, defaulting to the base level when unknown.
        extra = adjustments.get(normalized, 0.0)
        return float(self.base_discount + extra)
