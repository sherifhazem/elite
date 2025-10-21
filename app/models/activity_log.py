# -*- coding: utf-8 -*-
"""Activity Log model for tracking admin actions on companies."""

from datetime import datetime

from .. import db


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(
        db.String(100), nullable=False
    )  # e.g., 'Approved', 'Suspended', 'Correction Requested'
    notes = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    company = db.relationship("Company", backref="activity_logs", lazy=True)
