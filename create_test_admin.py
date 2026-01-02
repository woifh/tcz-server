#!/usr/bin/env python3
"""
Create a test admin user with known credentials for testing/development
"""
import sys
from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from app.models import Member

def create_test_admin():
    """Create a test admin user with predefined credentials"""
    
    # Test admin credentials
    firstname = "Test"
    lastname = "Admin"
    email = "admin@test.com"
    password = "admin123"
    
    app = create_app('development')
    
    with app.app_context():
        # Check if user already exists
        existing_user = Member.query.filter_by(email=email).first()
        if existing_user:
            print("=" * 60)
            print("✅ Test admin user already exists!")
            print("=" * 60)
            print()
            print("Login Credentials:")
            print(f"  Email: {email}")
            print(f"  Password: {password}")
            print()
            return
        
        # Create new test admin user
        admin = Member(
            firstname=firstname,
            lastname=lastname,
            email=email,
            role='administrator'
        )
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        
        print("=" * 60)
        print("✅ Test admin user created successfully!")
        print("=" * 60)
        print()
        print("Login Credentials:")
        print(f"  Email: {email}")
        print(f"  Password: {password}")
        print()
        print("You can now login to the application with these credentials.")
        print()

if __name__ == '__main__':
    try:
        create_test_admin()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)