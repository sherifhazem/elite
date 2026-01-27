"""Usage code model for partner-issued verification codes."""

from datetime import datetime

from app.core.database import db


class UsageCode(db.Model):
    """Represents a short-lived verification code issued by a partner."""

    __tablename__ = "usage_codes"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(5), nullable=False, index=True)
    partner_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    usage_count = db.Column(db.Integer, default=0, nullable=False)
    max_uses_per_window = db.Column(db.Integer, nullable=False)

    partner = db.relationship(
        "Company",
        foreign_keys=[partner_id],
        backref=db.backref("usage_codes", lazy="dynamic"),
        lazy="joined",
    )

    def is_expired(self) -> bool:
        """Return True when the usage code has expired."""

        return bool(self.expires_at and self.expires_at <= datetime.utcnow())

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<UsageCode {self.code} partner={self.partner_id}>"


__all__ = ["UsageCode"]
