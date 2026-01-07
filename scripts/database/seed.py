#!/usr/bin/env python3
"""
Seed database with initial data.

This creates the necessary initial records:
- 6 Courts (numbered 1-6)
- Admin user (if specified)

Usage:
    python seed_database.py
"""
import sys
import os
from pathlib import Path

# Load production environment variables before importing app
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / '.env.production'
    if env_file.exists():
        print(f"Loading environment from: {env_file}")
        load_dotenv(env_file)
    else:
        print("Warning: .env.production not found, using default .env")
        load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed")

from app import create_app, db
from app.models import Court, Member

def seed_database():
    """Seed database with initial data."""
    app = create_app('production')
    
    with app.app_context():
        print("=" * 60)
        print("Database Seeding Script")
        print("=" * 60)
        print()
        
        # Create courts
        print("Creating courts...")
        courts_created = 0
        for i in range(1, 7):  # Courts 1-6
            existing_court = Court.query.filter_by(number=i).first()
            if not existing_court:
                court = Court(number=i, status='available')
                db.session.add(court)
                courts_created += 1
                print(f"  ✓ Created Court {i}")
            else:
                print(f"  - Court {i} already exists")
        
        if courts_created > 0:
            db.session.commit()
            print(f"\n✓ Created {courts_created} courts")
        else:
            print("\n- All courts already exist")
        
        print()
        
        # Optionally create admin user
        admin_exists = Member.query.filter_by(role='administrator').first()
        
        if not admin_exists:
            print("No administrator found.")
            create_admin = input("Create an admin user? (yes/no): ").strip().lower()
            
            if create_admin == 'yes':
                print()
                firstname = input("Admin first name: ").strip()
                lastname = input("Admin last name: ").strip()
                email = input("Admin email: ").strip()
                password = input("Admin password: ").strip()
                
                admin = Member(
                    firstname=firstname,
                    lastname=lastname,
                    email=email,
                    role='administrator',
                    is_active=True
                )
                admin.set_password(password)
                db.session.add(admin)
                db.session.commit()
                
                print(f"\n✓ Created admin user: {firstname} {lastname} ({email})")
        else:
            print(f"✓ Administrator already exists: {admin_exists.name}")
        
        print()
        print("=" * 60)
        print("Database seeding complete!")
        print("=" * 60)
        print()
        
        # Show summary
        court_count = Court.query.count()
        member_count = Member.query.count()
        admin_count = Member.query.filter_by(role='administrator').count()
        
        print("Database summary:")
        print(f"  Courts: {court_count}")
        print(f"  Members: {member_count}")
        print(f"  Administrators: {admin_count}")
        print()
        
        return True

if __name__ == '__main__':
    try:
        success = seed_database()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
