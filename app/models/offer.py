"""Offer model describing discounts provided by partner companies.

Key fields:
- ``title`` and ``description``: Offer content details.
- ``base_discount``: Minimum discount applied to all members.
- ``start_date``: Optional activation date.
- ``valid_until``: Optional expiration timestamp.
- ``image_url``: Optional visual used to promote the offer.

Relationships:
- ``company``: Company that owns the offer.
- ``redemptions``: Redemptions generated from the offer.
"""

from datetime import datetime

from app.core.database import db


class Offer(db.Model):
    """Represents an offer provided by a company."""

    __tablename__ = "offers"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    # Store the minimum discount value that all users can access.
    base_discount = db.Column(db.Float, nullable=False, default=5.0)
    status = db.Column(db.String(20), nullable=False, default="active")
    start_date = db.Column(db.DateTime, nullable=True)
    valid_until = db.Column(db.DateTime, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
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
