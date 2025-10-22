# -*- coding: utf-8 -*-
"""Model for logging admin activities related to company management."""

from datetime import datetime
from app import db


class ActivityLog(db.Model):
    __tablename__ = "activity_log"

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, nullable=False)
    company_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    admin = db.relationship("User", foreign_keys=[admin_id], backref="activities", lazy="joined")
    company = db.relationship("Company", foreign_keys=[company_id], lazy="joined")

    def __repr__(self):
        return f"<ActivityLog {self.action} on company {self.company_id} by admin {self.admin_id}>"
