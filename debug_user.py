from app import create_app
from app.models import User

app = create_app()
with app.app_context():
    user = User.query.get(20)
    if user:
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Role: {user.role}")
        print(f"IsActive: {user.is_active}")
        print(f"CompanyID: {user.company_id}")
        print(f"Phone: {user.phone_number}")
        print(f"PhoneVerified: {user.is_phone_verified}")
    else:
        print("User 20 not found")
