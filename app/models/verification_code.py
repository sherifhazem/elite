from datetime import datetime, timedelta
from app.core.database import db

class VerificationCode(db.Model):
    """Store for OTP verification codes."""
    __tablename__ = "verification_codes"

    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), nullable=False, index=True)
    code = db.Column(db.String(10), nullable=False)
    # Purpose: 'registration', 'login', 'reset_password', 'verification'
    purpose = db.Column(db.String(50), nullable=False, default='verification')
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_used = db.Column(db.Boolean, default=False)

    @property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at

    def __repr__(self):
        return f"<VerificationCode {self.phone_number} - {self.code}>"
