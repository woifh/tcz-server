#!/usr/bin/env python3
"""
Test script to verify the grouping functionality for upcoming blocks.
This script creates test data and then tests the API endpoints.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Block, BlockReason, Court, Member
from datetime import datetime, date, time, timedelta
import json

def create_test_data():
    """Create test data for grouping functionality."""
    app = create_app()
    
    with app.app_context():
        # Create test admin user if not exists
        admin = Member.query.filter_by(email='woifh@gmx.at').first()
        if not admin:
            admin = Member(
                firstname='Test',
                lastname='Admin',
                email='woifh@gmx.at',
                password_hash='test_hash',
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
        
        # Create test reason if not exists
        reason = BlockReason.query.filter_by(name='Test Grund').first()
        if not reason:
            reason = BlockReason(
                name='Test Grund',
                created_by_id=admin.id
            )
            db.session.add(reason)
            db.session.commit()
        
        # Create test blocks for grouping
        tomorrow = date.today() + timedelta(days=1)
        day_after = date.today() + timedelta(days=2)
        
        # Test Case 1: Multi-court block (should be grouped)
        test_time = datetime.now()
        blocks_batch_1 = []
        for court_id in [1, 2, 3]:
            block = Block(
                court_id=court_id,
                date=tomorrow,
                start_time=time(10, 0),
                end_time=time(12, 0),
                reason_id=reason.id,
                details='Wartung',
                created_by_id=admin.id,
                created_at=test_time
            )
            blocks_batch_1.append(block)
            db.session.add(block)
        
        # Test Case 2: Single court block (should be separate)
        single_block = Block(
            court_id=4,
            date=tomorrow,
            start_time=time(14, 0),
            end_time=time(16, 0),
            reason_id=reason.id,
            details='Reparatur',
            created_by_id=admin.id,
            created_at=test_time + timedelta(minutes=5)
        )
        db.session.add(single_block)
        
        # Test Case 3: Another multi-court block (different time, should be separate group)
        test_time_2 = test_time + timedelta(minutes=10)
        blocks_batch_2 = []
        for court_id in [5, 6]:
            block = Block(
                court_id=court_id,
                date=day_after,
                start_time=time(9, 0),
                end_time=time(11, 0),
                reason_id=reason.id,
                details='Turnier',
                created_by_id=admin.id,
                created_at=test_time_2
            )
            blocks_batch_2.append(block)
            db.session.add(block)
        
        db.session.commit()
        
        print("Test data created successfully!")
        print(f"Batch 1: {len(blocks_batch_1)} blocks for courts 1,2,3 at {tomorrow} 10:00-12:00")
        print(f"Single: 1 block for court 4 at {tomorrow} 14:00-16:00")
        print(f"Batch 2: {len(blocks_batch_2)} blocks for courts 5,6 at {day_after} 09:00-11:00")
        
        return {
            'batch_1_ids': [b.id for b in blocks_batch_1],
            'single_id': single_block.id,
            'batch_2_ids': [b.id for b in blocks_batch_2]
        }

def test_api_grouping():
    """Test the API endpoint to see if grouping works."""
    import requests
    
    try:
        # Get upcoming blocks
        today = date.today().isoformat()
        next_month = (date.today() + timedelta(days=30)).isoformat()
        
        url = f"http://localhost:5002/admin/blocks?date_range_start={today}&date_range_end={next_month}"
        
        # Note: This will fail without authentication, but we can see the structure
        response = requests.get(url)
        print(f"API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            blocks = data.get('blocks', [])
            print(f"Found {len(blocks)} blocks")
            
            # Simulate the grouping logic
            groups = {}
            for block in blocks:
                key = f"{block['date']}_{block['start_time']}_{block['end_time']}_{block['reason_id']}_{block.get('details', '')}_{block['created_at']}"
                if key not in groups:
                    groups[key] = []
                groups[key].append(block)
            
            print(f"Grouped into {len(groups)} batches:")
            for i, (key, group_blocks) in enumerate(groups.items(), 1):
                court_numbers = [b['court_number'] for b in group_blocks]
                first_block = group_blocks[0]
                print(f"  Group {i}: Courts {court_numbers} - {first_block['date']} {first_block['start_time']}-{first_block['end_time']}")
        
        else:
            print(f"API call failed: {response.text}")
            
    except Exception as e:
        print(f"Error testing API: {e}")

if __name__ == '__main__':
    print("Creating test data for grouping functionality...")
    test_ids = create_test_data()
    print(f"Created test blocks with IDs: {test_ids}")
    
    print("\nTesting API grouping...")
    test_api_grouping()