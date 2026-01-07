#!/usr/bin/env python3
"""
Create a test block with the batch_id from the screenshot
"""

import sys
import os
from datetime import date, time

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Block, Member, BlockReason

def create_test_block():
    app = create_app()
    
    with app.app_context():
        batch_id = "1d40fb5c-500c-4127-9c4a-05d9f53fe47f"
        
        print(f"🔧 Creating test block with batch_id: {batch_id}")
        
        # Get or create a user (admin)
        user = Member.query.filter_by(role='admin').first()
        if not user:
            print("❌ No admin user found. Creating one...")
            user = Member(
                firstname="Test",
                lastname="Admin",
                email="admin@test.com",
                password_hash="dummy",
                role="admin"
            )
            db.session.add(user)
            db.session.commit()
            print(f"✅ Created admin user: {user.id}")
        else:
            print(f"✅ Using existing admin user: {user.id}")
        
        # Get or create a block reason
        reason = BlockReason.query.first()
        if not reason:
            print("❌ No block reason found. Creating one...")
            reason = BlockReason(
                name="Test Reason",
                description="Test reason for debugging"
            )
            db.session.add(reason)
            db.session.commit()
            print(f"✅ Created block reason: {reason.id}")
        else:
            print(f"✅ Using existing block reason: {reason.id}")
        
        # Create test blocks for multiple courts (like in the screenshot)
        courts = [1, 2, 3, 4, 5, 6]  # 6 courts as shown in screenshot
        
        for court_id in courts:
            # Check if block already exists
            existing = Block.query.filter_by(
                batch_id=batch_id,
                court_id=court_id
            ).first()
            
            if existing:
                print(f"⚠️ Block already exists for court {court_id}")
                continue
                
            block = Block(
                court_id=court_id,
                date=date(2026, 1, 4),  # Tomorrow
                start_time=time(8, 0),   # 08:00
                end_time=time(22, 0),    # 22:00
                reason_id=reason.id,
                details="Geplant",
                batch_id=batch_id,
                created_by_id=user.id
            )
            
            db.session.add(block)
            print(f"✅ Created block for court {court_id}")
        
        db.session.commit()
        
        # Verify the blocks were created
        blocks = Block.query.filter_by(batch_id=batch_id).all()
        print(f"\n📊 Verification: Found {len(blocks)} blocks with batch_id {batch_id}")
        
        for block in blocks:
            print(f"  Block {block.id}: Court {block.court_id}, Date {block.date}")
        
        print(f"\n✅ Test data created successfully!")
        print(f"🔗 You can now test the edit URL: http://127.0.0.1:5001/admin/court-blocking/{batch_id}")

if __name__ == "__main__":
    create_test_block()