# -*- coding: utf-8 -*-
"""Model for logging admin activities related to company management."""

from datetime import datetime
from app.core.database import db


class ActivityLog(db.Model):
    """Audit log entry tracking administrative actions on companies."""

    __tablename__ = "activity_log"

    id = db.Column(db.Integer, primary_key=True)

    # ✅ إضافة المفاتيح الأجنبية بشكل صحيح
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)

    action = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # ✅ العلاقات مصححة ومحددة بوضوح
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

    def __repr__(self):
        return f"<ActivityLog {self.action} on company {self.company_id} by admin {self.admin_id}>"
