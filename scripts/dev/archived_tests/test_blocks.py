#!/usr/bin/env python3
"""Test script to create block reasons and test blocks."""
import os
import sys
from datetime import date, time, datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Member, Court, BlockReason, Block

def create_test_data():
    """Create test block reasons and blocks."""
    app = create_app('development')
    
    with app.app_context():
        print("Creating test block reasons and blocks...")
        
        # Get admin user
        admin = Member.query.filter_by(role='administrator').first()
        if not admin:
            print("No admin user found!")
            return
        
        print(f"Using admin: {admin.name}")
        
        # Create block reasons if they don't exist
        reasons_data = [
            ('Wartung', 'Platzwartung und Instandhaltung'),
            ('Wetter', 'Witterungsbedingte Sperrung'),
            ('Turnier', 'Turnier oder Veranstaltung'),
            ('Kurs', 'Tennisstunde oder Kurs'),
            ('Reparatur', 'Reparaturarbeiten')
        ]
        
        for reason_name, description in reasons_data:
            existing = BlockReason.query.filter_by(name=reason_name).first()
            if not existing:
                reason = BlockReason(
                    name=reason_name,
                    created_by_id=admin.id
                )
                db.session.add(reason)
                print(f"Created block reason: {reason_name}")
        
        db.session.commit()
        
        # Create some test blocks for today and tomorrow
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        # Get courts
        courts = Court.query.all()
        if not courts:
            print("No courts found!")
            return
        
        # Get block reasons
        wartung = BlockReason.query.filter_by(name='Wartung').first()
        wetter = BlockReason.query.filter_by(name='Wetter').first()
        turnier = BlockReason.query.filter_by(name='Turnier').first()
        
        # Create test blocks
        test_blocks = [
            {
                'court_id': courts[0].id,  # Court 1
                'date': today,
                'start_time': time(10, 0),
                'end_time': time(12, 0),
                'reason_id': wartung.id,
                'details': 'Linien neu ziehen'
            },
            {
                'court_id': courts[1].id,  # Court 2
                'date': today,
                'start_time': time(14, 0),
                'end_time': time(16, 0),
                'reason_id': wetter.id,
                'details': 'Platz zu nass nach Regen'
            },
            {
                'court_id': courts[2].id,  # Court 3
                'date': tomorrow,
                'start_time': time(9, 0),
                'end_time': time(18, 0),
                'reason_id': turnier.id,
                'details': 'Vereinsmeisterschaft'
            }
        ]
        
        for block_data in test_blocks:
            # Check if block already exists
            existing = Block.query.filter_by(
                court_id=block_data['court_id'],
                date=block_data['date'],
                start_time=block_data['start_time']
            ).first()
            
            if not existing:
                block = Block(
                    court_id=block_data['court_id'],
                    date=block_data['date'],
                    start_time=block_data['start_time'],
                    end_time=block_data['end_time'],
                    reason_id=block_data['reason_id'],
                    details=block_data['details'],
                    created_by_id=admin.id
                )
                db.session.add(block)
                print(f"Created block: Court {block_data['court_id']}, {block_data['date']} {block_data['start_time']}-{block_data['end_time']}")
        
        db.session.commit()
        
        # List all blocks
        blocks = Block.query.all()
        print(f"\nAll blocks ({len(blocks)}):")
        for block in blocks:
            reason_name = block.reason_obj.name if block.reason_obj else 'Unknown'
            print(f"  Block {block.id}: Court {block.court_id}, {block.date} {block.start_time}-{block.end_time}")
            print(f"    Reason: {reason_name}")
            print(f"    Details: {block.details}")
        
        print("\nTest data created successfully!")

if __name__ == '__main__':
    create_test_data()