from datetime import datetime

from app.core.database import db


class AdminSetting(db.Model):
    """Key-value storage for admin-managed configuration blocks."""

    __tablename__ = "admin_settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), nullable=False, unique=True, index=True)
    value = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<AdminSetting {self.key}>"


__all__ = ["AdminSetting"]
