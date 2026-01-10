# -*- coding: utf-8 -*-
"""Model for logging administrative actions and usage verification attempts."""

from datetime import datetime
from app.core.database import db


class ActivityLog(db.Model):
    """Audit log entry tracking administrative actions and usage attempts."""

    __tablename__ = "activity_log"

    id = db.Column(db.Integer, primary_key=True)

    # ✅ Administrative activity fields
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)

    action = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # ✅ Usage verification attempt fields
    member_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    partner_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)
    offer_id = db.Column(db.Integer, db.ForeignKey("offers.id"), nullable=True)
    code_used = db.Column(db.String(8), nullable=True)
    result = db.Column(db.String(32), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)

    # ✅ Administrative relationships
    admin = db.relationship(
        "User",
        foreign_keys=[admin_id],
        backref=db.backref("activity_logs", lazy="dynamic"),
        lazy="joined",
    )
    company = db.relationship(
        "Company",
        foreign_keys=[company_id],
        backref=db.backref("activity_logs", lazy="dynamic"),
        lazy="joined",
    )
    # ✅ Usage verification relationships
    member = db.relationship(
        "User",
        foreign_keys=[member_id],
        backref=db.backref("usage_attempts", lazy="dynamic"),
        lazy="joined",
    )
    partner = db.relationship(
        "Company",
        foreign_keys=[partner_id],
        backref=db.backref("usage_attempts", lazy="dynamic"),
        lazy="joined",
    )
    offer = db.relationship(
        "Offer",
        foreign_keys=[offer_id],
        backref=db.backref("usage_attempts", lazy="dynamic"),
        lazy="joined",
    )

    def __repr__(self) -> str:
        summary = f"{self.action}"
        if self.member_id:
            summary = f"{summary} member={self.member_id}"
        if self.partner_id:
            summary = f"{summary} partner={self.partner_id}"
        return f"<ActivityLog {summary}>"
