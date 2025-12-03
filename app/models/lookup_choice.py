from datetime import datetime

from app.core.database import db


class LookupChoice(db.Model):
    """Centralized lookup values for managed lists such as cities and industries."""

    __tablename__ = "lookup_choices"
    __table_args__ = (
        db.UniqueConstraint("list_type", "name", name="uq_lookup_choices_type_name"),
    )

    id = db.Column(db.Integer, primary_key=True)
    list_type = db.Column(db.String(32), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<LookupChoice {self.list_type}:{self.name} active={self.active}>"


__all__ = ["LookupChoice"]
