#!/usr/bin/env python3
"""
Simple test to verify batch_id assignment
"""

import requests
from datetime import datetime, date, timedelta
import json

def test_batch_id_assignment():
    """Test that multi-court blocks get proper batch_id assignment."""
    
    session = requests.Session()
    
    # Login
    login_data = {'email': 'woifh@gmx.at', 'password': 'test123'}
    login_response = session.post('http://localhost:5002/auth/login', data=login_data)
    
    if login_response.status_code != 200 or 'login' in login_response.url.lower():
        print("Login failed")
        return False
    
    print("✓ Login successful")
    
    # Create a multi-court block
    tomorrow = (date.today() + timedelta(days=2)).isoformat()
    
    multi_court_data = {
        'court_ids': [1, 2, 3],  # Multiple courts - should get batch_id
        'date': tomorrow,
        'start_time': '15:00',
        'end_time': '17:00',
        'reason_id': 1,
        'details': 'Batch ID Test'
    }
    
    create_response = session.post(
        'http://localhost:5002/admin/blocks/multi-court',
        json=multi_court_data,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Create response: {create_response.status_code}")
    if create_response.status_code == 201:
        print("✓ Multi-court blocks created")
        
        # Get the blocks to check batch_id
        today = date.today().isoformat()
        next_week = (date.today() + timedelta(days=7)).isoformat()
        
        blocks_response = session.get(
            f'http://localhost:5002/admin/blocks?date_range_start={today}&date_range_end={next_week}'
        )
        
        if blocks_response.status_code == 200:
            blocks_data = blocks_response.json()
            blocks = blocks_data.get('blocks', [])
            
            # Find our test blocks (only the most recent ones)
            test_blocks = [b for b in blocks if b.get('details') == 'Batch ID Test']
            print(f"Found {len(test_blocks)} test blocks")
            
            # Sort by ID to get the most recent ones
            test_blocks.sort(key=lambda x: x['id'])
            
            for block in test_blocks:
                print(f"  Block {block['id']}: Court {block['court_number']}, batch_id: {block.get('batch_id', 'None')}")
            
            # Check if the most recent 3 blocks have the same batch_id
            if len(test_blocks) >= 3:
                recent_blocks = test_blocks[-3:]  # Get the last 3 blocks
                batch_ids = [b.get('batch_id') for b in recent_blocks]
                unique_batch_ids = set(batch_ids)
                
                if len(unique_batch_ids) == 1 and list(unique_batch_ids)[0] is not None:
                    print(f"✓ All recent blocks have the same batch_id: {list(unique_batch_ids)[0]}")
                    
                    # Test the batch edit URL
                    batch_id = list(unique_batch_ids)[0]
                    edit_url = f"http://localhost:5002/admin/court-blocking/batch_{batch_id}"
                    edit_response = session.get(edit_url)
                    print(f"Edit URL test: {edit_response.status_code}")
                    
                    if edit_response.status_code == 200:
                        print("✓ Batch edit URL works!")
                        return True
                    else:
                        print(f"✗ Batch edit URL failed: {edit_response.text[:200]}")
                else:
                    print(f"✗ Recent blocks have different batch_ids: {batch_ids}")
            else:
                print("✗ Not enough test blocks found")
        else:
            print(f"✗ Failed to get blocks: {blocks_response.status_code}")
    else:
        print(f"✗ Failed to create blocks: {create_response.text}")
    
    return False

if __name__ == '__main__':
    print("Testing batch_id assignment...")
    success = test_batch_id_assignment()
    
    if success:
        print("\n✓ Batch ID functionality working correctly!")
    else:
        print("\n✗ Batch ID functionality has issues.")