#!/usr/bin/env python3
"""
Test to verify single court blocks also get batch_id assignment
"""

import requests
from datetime import datetime, date, timedelta
import json

def test_single_block_batch_id():
    """Test that single court blocks also get batch_id assignment."""
    
    session = requests.Session()
    
    # Login
    login_data = {'email': 'woifh@gmx.at', 'password': 'test123'}
    login_response = session.post('http://localhost:5002/auth/login', data=login_data)
    
    if login_response.status_code != 200 or 'login' in login_response.url.lower():
        print("Login failed")
        return False
    
    print("✓ Login successful")
    
    # Create a single court block using the multi-court endpoint
    tomorrow = (date.today() + timedelta(days=3)).isoformat()
    
    single_court_data = {
        'court_ids': [4],  # Single court - should still get batch_id
        'date': tomorrow,
        'start_time': '16:00',
        'end_time': '18:00',
        'reason_id': 1,
        'details': 'Single Batch ID Test'
    }
    
    create_response = session.post(
        'http://localhost:5002/admin/blocks/multi-court',
        json=single_court_data,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Create response: {create_response.status_code}")
    if create_response.status_code == 201:
        print("✓ Single court block created")
        
        # Get the blocks to check batch_id
        today = date.today().isoformat()
        next_week = (date.today() + timedelta(days=7)).isoformat()
        
        blocks_response = session.get(
            f'http://localhost:5002/admin/blocks?date_range_start={today}&date_range_end={next_week}'
        )
        
        if blocks_response.status_code == 200:
            blocks_data = blocks_response.json()
            blocks = blocks_data.get('blocks', [])
            
            # Find our test block
            test_blocks = [b for b in blocks if b.get('details') == 'Single Batch ID Test']
            print(f"Found {len(test_blocks)} test blocks")
            
            for block in test_blocks:
                print(f"  Block {block['id']}: Court {block['court_number']}, batch_id: {block.get('batch_id', 'None')}")
            
            # Check if the single block has a batch_id
            if test_blocks:
                block = test_blocks[0]
                batch_id = block.get('batch_id')
                
                if batch_id is not None:
                    print(f"✓ Single block has batch_id: {batch_id}")
                    
                    # Test the batch edit URL
                    edit_url = f"http://localhost:5002/admin/court-blocking/batch_{batch_id}"
                    edit_response = session.get(edit_url)
                    print(f"Edit URL test: {edit_response.status_code}")
                    
                    if edit_response.status_code == 200:
                        print("✓ Single block batch edit URL works!")
                        return True
                    else:
                        print(f"✗ Batch edit URL failed: {edit_response.text[:200]}")
                else:
                    print("✗ Single block has no batch_id")
            else:
                print("✗ No test blocks found")
        else:
            print(f"✗ Failed to get blocks: {blocks_response.status_code}")
    else:
        print(f"✗ Failed to create block: {create_response.text}")
    
    return False

if __name__ == '__main__':
    print("Testing single block batch_id assignment...")
    success = test_single_block_batch_id()
    
    if success:
        print("\n✓ Single block batch ID functionality working correctly!")
    else:
        print("\n✗ Single block batch ID functionality has issues.")