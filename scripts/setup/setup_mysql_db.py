#!/usr/bin/env python3
"""
MySQL Database Setup Script for PythonAnywhere
Creates all necessary tables and initial data for the tennis club application.
"""

import os
import sys
from werkzeug.security import generate_password_hash

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Setting up MySQL database tables...")
print("=" * 40)

try:
    from app import create_app, db
    from app.models import Member, Court, BlockReason
    print("✓ Imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

# Create Flask app
app = create_app()
print("✓ Flask app created")

with app.app_context():
    print("✓ App context active")
    
    # Print database URL (without password)
    db_url = app.config.get('DATABASE_URL', 'Not set')
    if 'mysql' in db_url and '@' in db_url:
        # Hide password in URL for security
        parts = db_url.split('@')
        if len(parts) == 2:
            user_pass = parts[0].split('//')[-1]
            if ':' in user_pass:
                user = user_pass.split(':')[0]
                db_url_safe = f"mysql+pymysql://{user}:***@{parts[1]}"
            else:
                db_url_safe = db_url
        else:
            db_url_safe = db_url
    else:
        db_url_safe = db_url
    print(f"Database URL: {db_url_safe}")
    
    # Create all tables
    print("Creating database tables...")
    try:
        db.create_all()
        print("✓ Tables created")
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        sys.exit(1)
    
    # Create admin user if it doesn't exist
    print("Creating admin user...")
    try:
        admin = Member.query.filter_by(email='max@mustermann.at').first()
        if not admin:
            admin = Member(
                firstname='Max',
                lastname='Mustermann',
                email='max@mustermann.at',
                password_hash=generate_password_hash('max@mustermann.at'),
                role='administrator'
            )
            db.session.add(admin)
            print("✓ Admin user created")
        else:
            print("✓ Admin user exists")
    except Exception as e:
        print(f"✗ Error creating admin user: {e}")
        sys.exit(1)
    
    # Create courts if they don't exist
    print("Creating courts...")
    try:
        court_count = Court.query.count()
        if court_count == 0:
            for i in range(1, 7):  # Courts 1-6
                court = Court(number=i, status='available')
                db.session.add(court)
            print("✓ 6 courts created")
        else:
            print(f"✓ {court_count} courts exist")
    except Exception as e:
        print(f"✗ Error creating courts: {e}")
        sys.exit(1)
    
    # Create default block reasons if they don't exist
    print("Creating block reasons...")
    try:
        reason_count = BlockReason.query.count()
        if reason_count == 0:
            default_reasons = [
                'Maintenance',
                'Weather',
                'Tournament',
                'Private Event',
                'Repair'
            ]
            for reason_name in default_reasons:
                reason = BlockReason(
                    name=reason_name,
                    is_active=True,
                    created_by_id=admin.id if admin else 1
                )
                db.session.add(reason)
            print("✓ 5 block reasons created")
        else:
            print(f"✓ {reason_count} block reasons exist")
    except Exception as e:
        print(f"✗ Error creating block reasons: {e}")
        sys.exit(1)
    
    # Commit all changes
    try:
        db.session.commit()
        print("✓ Changes committed")
    except Exception as e:
        print(f"✗ Error committing changes: {e}")
        db.session.rollback()
        sys.exit(1)
    
    # Print final counts
    print("Final counts:")
    try:
        member_count = Member.query.count()
        court_count = Court.query.count()
        reason_count = BlockReason.query.count()
        print(f"  Members: {member_count}")
        print(f"  Courts: {court_count}")
        print(f"  Block Reasons: {reason_count}")
    except Exception as e:
        print(f"✗ Error getting counts: {e}")

print("✅ Database is ready!")