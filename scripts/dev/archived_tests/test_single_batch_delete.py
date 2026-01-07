#!/usr/bin/env python3
"""
Test to verify single court batch delete functionality
"""

import requests
from datetime import datetime, date, timedelta
import json

def test_single_batch_delete():
    """Test that single court blocks can be deleted via batch delete."""
    
    session = requests.Session()
    
    # Login
    login_data = {'email': 'woifh@gmx.at', 'password': 'test123'}
    login_response = session.post('http://localhost:5002/auth/login', data=login_data)
    
    if login_response.status_code != 200 or 'login' in login_response.url.lower():
        print("✗ Login failed")
        return False
    
    print("✓ Login successful")
    
    # Create a single court block for testing
    tomorrow = (date.today() + timedelta(days=7)).isoformat()
    test_identifier = f"Single Batch Delete Test {datetime.now().strftime('%H%M%S')}"
    
    single_court_data = {
        'court_ids': [4],  # Single court
        'date': tomorrow,
        'start_time': '11:00',
        'end_time': '13:00',
        'reason_id': 1,
        'details': test_identifier
    }
    
    create_response = session.post(
        'http://localhost:5002/admin/blocks/multi-court',
        json=single_court_data,
        headers={'Content-Type': 'application/json'}
    )
    
    if create_response.status_code != 201:
        print(f"✗ Failed to create test block: {create_response.status_code}")
        return False
    
    print("✓ Test block created")
    
    # Get the block to find the batch_id
    today = date.today().isoformat()
    next_week = (date.today() + timedelta(days=8)).isoformat()
    
    blocks_response = session.get(
        f'http://localhost:5002/admin/blocks?date_range_start={today}&date_range_end={next_week}'
    )
    
    if blocks_response.status_code != 200:
        print(f"✗ Failed to get blocks: {blocks_response.status_code}")
        return False
    
    blocks_data = blocks_response.json()
    blocks = blocks_data.get('blocks', [])
    
    # Find our test block
    test_blocks = [b for b in blocks if b.get('details') == test_identifier]
    
    if len(test_blocks) != 1:
        print(f"✗ Expected 1 test block, found {len(test_blocks)}")
        return False
    
    # Get the batch_id
    batch_id = test_blocks[0].get('batch_id')
    if not batch_id:
        print("✗ Test block has no batch_id")
        return False
    
    print(f"✓ Found test block with batch_id: {batch_id}")
    
    # Delete the batch (which contains only one block)
    delete_response = session.delete(f'http://localhost:5002/admin/blocks/batch/{batch_id}')
    
    if delete_response.status_code != 200:
        print(f"✗ Failed to delete batch: {delete_response.status_code}")
        print(f"Response: {delete_response.text}")
        return False
    
    delete_data = delete_response.json()
    print(f"✓ Batch deleted: {delete_data.get('message', 'Success')}")
    
    # Verify the block is deleted
    blocks_response = session.get(
        f'http://localhost:5002/admin/blocks?date_range_start={today}&date_range_end={next_week}'
    )
    
    if blocks_response.status_code != 200:
        print(f"✗ Failed to get blocks after deletion: {blocks_response.status_code}")
        return False
    
    blocks_data = blocks_response.json()
    blocks = blocks_data.get('blocks', [])
    
    # Check that no test blocks remain
    remaining_test_blocks = [b for b in blocks if b.get('details') == test_identifier]
    
    if len(remaining_test_blocks) > 0:
        print(f"✗ {len(remaining_test_blocks)} test blocks still exist after batch delete")
        return False
    
    print("✓ Single block successfully deleted via batch delete")
    
    return True

if __name__ == '__main__':
    print("Testing single court batch delete functionality...")
    success = test_single_batch_delete()
    
    if success:
        print("\n✓ Single court batch delete functionality working correctly!")
    else:
        print("\n✗ Single court batch delete functionality has issues.")