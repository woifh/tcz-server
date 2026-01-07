#!/usr/bin/env python3
"""Create test user for local development"""
import os
# Use the .env file configuration
from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from app.models import Member, Court

app = create_app('development')

with app.app_context():
    # Create tables
    db.create_all()
    
    # Create 6 courts
    for i in range(1, 7):
        if not Court.query.filter_by(number=i).first():
            court = Court(number=i, status='available')
            db.session.add(court)
    
    # Create test admin user
    admin = Member.query.filter_by(email='admin@gmail.com').first()
    if not admin:
        admin = Member(
            firstname='Admin',
            lastname='User',
            email='admin@gmail.com',
            role='administrator'
        )
        admin.set_password('admin123')
        db.session.add(admin)
    
    # Create test member user
    member = Member.query.filter_by(email='member@gmail.com').first()
    if not member:
        member = Member(
            firstname='Test',
            lastname='Member',
            email='member@gmail.com',
            role='member'
        )
        member.set_password('member123')
        db.session.add(member)
    
    db.session.commit()
    
    print("✅ Database initialized successfully!")
    print("\nTest Users Created:")
    print("=" * 50)
    print("Admin User:")
    print("  Email: admin@gmail.com")
    print("  Password: admin123")
    print("\nMember User:")
    print("  Email: member@gmail.com")
    print("  Password: member123")
    print("=" * 50)
