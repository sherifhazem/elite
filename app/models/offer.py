"""Offer model describing discounts provided by partner companies.

Key fields:
- ``title`` and ``description``: Offer content details.
"""
from datetime import datetime
from app.core.database import db

OFFER_CLASSIFICATION_TYPES = (
    "first_time_offer",
    "loyalty_offer",
    "active_members_only",
    "happy_hour",
    "mid_week",
)


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



    classifications = db.relationship(
        "OfferClassification",
        back_populates="offer",
        cascade="all, delete-orphan",
        order_by="OfferClassification.classification",
    )

    def __repr__(self) -> str:
        """Return a string representation for debugging."""

        return f"<Offer {self.title} - base {self.base_discount}%>"

    def get_discount_for_level(self, level: str) -> float:
        """Return the discount including the configured membership adjustment."""
        # TODO: Incentives will be calculated based on verified usage.
        return float(self.base_discount or 0.0)

    @property
    def classification_values(self) -> list[str]:
        """Return the stored classification keys for template convenience."""

        return [record.classification for record in self.classifications]


class OfferClassification(db.Model):
    """Represents a single classification label attached to an offer."""

    __tablename__ = "offer_classifications"

    id = db.Column(db.Integer, primary_key=True)
    offer_id = db.Column(db.Integer, db.ForeignKey("offers.id"), nullable=False)
    classification = db.Column(db.String(50), nullable=False)

    offer = db.relationship("Offer", back_populates="classifications")

    __table_args__ = (
        db.UniqueConstraint(
            "offer_id", "classification", name="uq_offer_classifications_offer_id"
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<OfferClassification {self.classification}>"
