#!/usr/bin/env python3
"""
Create default block reasons for the Tennis Club Reservation System.
"""
import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Member, BlockReason


def create_default_reasons():
    """Create default block reasons."""
    print("Creating default block reasons...")
    
    # Create app
    app = create_app(os.environ.get('FLASK_ENV', 'development'))
    
    with app.app_context():
        # Get the first admin user
        admin = Member.query.filter_by(role='administrator').first()
        if not admin:
            print("❌ No admin user found. Please create an admin user first.")
            return False
        
        # Default reasons to create
        default_reasons = [
            'Wartung',
            'Wetter',
            'Turnier',
            'Meisterschaft',
            'Tenniskurs',
            'Veranstaltung'
        ]
        
        created_count = 0
        
        for reason_name in default_reasons:
            # Check if reason already exists
            existing_reason = BlockReason.query.filter_by(name=reason_name).first()
            if not existing_reason:
                reason = BlockReason(
                    name=reason_name,
                    is_active=True,
                    created_by_id=admin.id
                )
                db.session.add(reason)
                created_count += 1
                print(f"  ✓ Created reason: {reason_name}")
            else:
                print(f"  ℹ Reason already exists: {reason_name}")
        
        if created_count > 0:
            db.session.commit()
            print(f"\n✅ Created {created_count} new block reasons")
        else:
            print("\n✅ All default reasons already exist")
        
        # List all reasons
        all_reasons = BlockReason.query.filter_by(is_active=True).all()
        print(f"\nTotal active block reasons: {len(all_reasons)}")
        for reason in all_reasons:
            print(f"  - {reason.name}")
        
        return True


if __name__ == '__main__':
    create_default_reasons()