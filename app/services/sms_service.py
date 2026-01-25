from TaqnyatSms import client as TaqnyatClient
from app.models import SMSLog, VerificationCode, db
from flask import current_app
from datetime import datetime, timedelta
import random

class SMSService:
    def __init__(self):
        # We should ideally move these to config, but for now using constants as per user sample
        self.bearer_token = '78fadbffb8d0f05434c0189f6d9cbf9f'
        self.sender_name = 'HENTAUTO'
        self.client = TaqnyatClient(self.bearer_token)

    def send_sms(self, recipient, message):
        """Send a general SMS message."""
        try:
            # Taqnyat expects list of recipients
            response = self.client.sendMsg(message, [recipient], self.sender_name, None)
            
            # Log the message
            self._log_sms(recipient, message, response)
            
            return response
        except Exception as e:
            current_app.logger.error(f"Failed to send SMS to {recipient}: {e}")
            return None

    def send_otp(self, recipient: str, purpose: str = 'verification'):
        """Generate and send an OTP."""
        code = self._generate_code()
        message = f"رمز التحقق للنخبه هو: {code}"
        
        # Save code to DB
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        verification = VerificationCode(
            phone_number=recipient,
            code=code,
            purpose=purpose,
            expires_at=expires_at
        )
        db.session.add(verification)
        db.session.commit()
        
        # Send SMS
        return self.send_sms(recipient, message)

    def verify_otp(self, phone_number: str, code: str, purpose: str = 'verification') -> bool:
        """Verify the provided OTP."""
        verification = VerificationCode.query.filter_by(
            phone_number=phone_number,
            code=code,
            purpose=purpose,
            is_used=False
        ).filter(VerificationCode.expires_at > datetime.utcnow()).first()

        if verification:
            verification.is_used = True
            db.session.commit()
            return True
        return False

    def send_welcome(self, recipient: str):
        """Send welcome message."""
        message = "مرحباً بك في إليت! شكراً لتسجيلك معنا. نأمل أن تستمتع بتجربتك."
        return self.send_sms(recipient, message)
        
    def send_password_reset(self, recipient: str, token: str):
        """Send password reset link via SMS."""
        # Note: We use request context in routes.py to generate URIs, 
        # but here we just need the token and base url.
        # It's better to pass the full URL from the route.
        pass

    def send_password_reset_link(self, recipient: str, reset_url: str):
        """Send password reset link to user's phone."""
        message = f"رابط إعادة تعيين كلمة المرور لـ ELITE: {reset_url}"
        return self.send_sms(recipient, message)

    def _generate_code(self):
        return str(random.randint(1000, 9999))

    def _log_sms(self, recipient, message, response):
        """Log SMS details to database."""
        try:
            # Response format from user sample:
            # {"statusCode":201,"messageId":9108233203,"cost":"0.0800","currency":"SAR","totalCount":1,"msgLength":1,"accepted":"[966597988313,]","rejected":"[]"}
            # It might be a dict or string, user sample shows string rep? 
            # sms_test.py prints it. Taqnyat library usually returns dict or json.
            
            status_code = response.get('statusCode') if isinstance(response, dict) else None
            message_id = str(response.get('messageId')) if isinstance(response, dict) else None
            cost = str(response.get('cost')) if isinstance(response, dict) else None
            currency = str(response.get('currency')) if isinstance(response, dict) else None
            
            log = SMSLog(
                recipient=recipient,
                message=message,
                status_code=status_code,
                message_id=message_id,
                cost=cost,
                currency=currency
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Failed to log SMS: {e}")
