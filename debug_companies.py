from app import create_app
from app.models import Company, User

app = create_app()
with app.app_context():
    companies = Company.query.all()
    print("Companies:")
    for c in companies:
        print(f"ID: {c.id}, Name: {c.name}, OwnerID: {c.owner_user_id}, Status: {c.status}")
        owner = User.query.get(c.owner_user_id)
        if owner:
            print(f"  Owner: {owner.username}, Role: {owner.role}")
        else:
            print("  Owner not found")

    print("\nUsers with role 'company':")
    company_users = User.query.filter_by(role='company').all()
    for u in company_users:
        print(f"ID: {u.id}, Username: {u.username}, Role: {u.role}, CompanyID: {u.company_id}")
