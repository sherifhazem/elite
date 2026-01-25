from datetime import datetime
from app.core.database import db

class SMSLog(db.Model):
    """Log of sent SMS messages."""
    __tablename__ = "sms_logs"

    id = db.Column(db.Integer, primary_key=True)
    recipient = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status_code = db.Column(db.Integer, nullable=True)
    message_id = db.Column(db.String(50), nullable=True)
    cost = db.Column(db.String(20), nullable=True)
    currency = db.Column(db.String(10), nullable=True)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Optional: Link to user if available
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    user = db.relationship("User", backref=db.backref("sms_logs", lazy="dynamic"))

    def __repr__(self):
        return f"<SMSLog {self.recipient} - {self.status_code}>"
