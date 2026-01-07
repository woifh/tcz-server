#!/usr/bin/env python3
"""
Database initialization script for Tennis Club Reservation System.

This script creates all database tables, populates initial data (6 courts),
and optionally creates an admin user.
"""
import sys
import os
from getpass import getpass

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Member, Court


def init_database():
    """Initialize the database with tables and initial data."""
    print("Tennis Club Reservation System - Database Initialization")
    print("=" * 60)
    
    # Create app
    app = create_app(os.environ.get('FLASK_ENV', 'development'))
    
    with app.app_context():
        print("\n1. Creating database tables...")
        try:
            db.create_all()
            print("   ✓ Tables created successfully")
        except Exception as e:
            print(f"   ✗ Error creating tables: {e}")
            return False
        
        print("\n2. Initializing courts...")
        try:
            # Check if courts already exist
            existing_courts = Court.query.count()
            if existing_courts > 0:
                print(f"   ℹ Courts already initialized ({existing_courts} courts exist)")
            else:
                # Create 6 courts
                for i in range(1, 7):
                    court = Court(number=i, status='available')
                    db.session.add(court)
                db.session.commit()
                print("   ✓ Created 6 tennis courts (1-6)")
        except Exception as e:
            print(f"   ✗ Error initializing courts: {e}")
            db.session.rollback()
            return False
        
        print("\n3. Creating admin user...")
        try:
            # Check if admin already exists
            existing_admin = Member.query.filter_by(role='administrator').first()
            if existing_admin:
                print(f"   ℹ Admin user already exists: {existing_admin.email}")
                create_new = input("   Create another admin user? (y/n): ").lower() == 'y'
                if not create_new:
                    print("\n✓ Database initialization complete!")
                    return True
            
            # Get admin details
            print("\n   Enter admin user details:")
            firstname = input("   First name: ").strip()
            lastname = input("   Last name: ").strip()
            email = input("   Email: ").strip()
            
            # Check if email already exists
            if Member.query.filter_by(email=email).first():
                print(f"   ✗ User with email {email} already exists")
                return False
            
            password = getpass("   Password: ")
            password_confirm = getpass("   Confirm password: ")
            
            if password != password_confirm:
                print("   ✗ Passwords do not match")
                return False
            
            if len(password) < 8:
                print("   ✗ Password must be at least 8 characters")
                return False
            
            # Create admin user
            admin = Member(firstname=firstname, lastname=lastname, email=email, role='administrator')
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            
            print(f"   ✓ Admin user created: {firstname} {lastname} ({email})")
            
        except Exception as e:
            print(f"   ✗ Error creating admin user: {e}")
            db.session.rollback()
            return False
        
        print("\n" + "=" * 60)
        print("✓ Database initialization complete!")
        print("\nYou can now start the application with:")
        print("  flask run")
        print("\nOr deploy to PythonAnywhere following DEPLOYMENT.md")
        
        return True


def reset_database():
    """Reset the database (drop all tables and recreate)."""
    print("⚠️  WARNING: This will delete ALL data in the database!")
    confirm = input("Are you sure you want to reset the database? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("Reset cancelled.")
        return
    
    app = create_app(os.environ.get('FLASK_ENV', 'development'))
    
    with app.app_context():
        print("\nDropping all tables...")
        db.drop_all()
        print("✓ All tables dropped")
        
        print("\nRecreating tables...")
        db.create_all()
        print("✓ Tables recreated")
        
        print("\nDatabase reset complete. Run init_db.py to populate initial data.")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--reset':
        reset_database()
    else:
        init_database()
