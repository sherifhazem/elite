"""Offer model definition."""

from datetime import datetime

from app import db


class Offer(db.Model):
    """Represents an offer provided by a company."""

    __tablename__ = "offers"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    discount_percent = db.Column(db.Float, nullable=False)
    valid_until = db.Column(db.DateTime, nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Establish relationship with Company for easy access to related offers
    company = db.relationship("Company", backref="offers")

    def __repr__(self) -> str:
        """Return a string representation for debugging."""

        return f"<Offer {self.title} - {self.discount_percent}%>"
