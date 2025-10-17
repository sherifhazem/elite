"""Company model definition."""

from datetime import datetime

from .. import db


class Company(db.Model):
    """Represents a company collaborating with ELITE."""

    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        """Return a string representation for debugging."""

        return f"<Company {self.name}>"
