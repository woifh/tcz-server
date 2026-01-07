#!/usr/bin/env python3
"""
Test to verify batch delete functionality
"""

import requests
from datetime import datetime, date, timedelta
import json

def test_batch_delete():
    """Test that batch delete removes entire batch."""
    
    session = requests.Session()
    
    # Login
    login_data = {'email': 'woifh@gmx.at', 'password': 'test123'}
    login_response = session.post('http://localhost:5002/auth/login', data=login_data)
    
    if login_response.status_code != 200 or 'login' in login_response.url.lower():
        print("✗ Login failed")
        return False
    
    print("✓ Login successful")
    
    # Create a multi-court block for testing
    tomorrow = (date.today() + timedelta(days=6)).isoformat()
    test_identifier = f"Batch Delete Test {datetime.now().strftime('%H%M%S')}"
    
    multi_court_data = {
        'court_ids': [1, 2, 3],
        'date': tomorrow,
        'start_time': '13:00',
        'end_time': '15:00',
        'reason_id': 1,
        'details': test_identifier
    }
    
    create_response = session.post(
        'http://localhost:5002/admin/blocks/multi-court',
        json=multi_court_data,
        headers={'Content-Type': 'application/json'}
    )
    
    if create_response.status_code != 201:
        print(f"✗ Failed to create test blocks: {create_response.status_code}")
        return False
    
    print("✓ Test blocks created")
    
    # Get the blocks to find the batch_id
    today = date.today().isoformat()
    next_week = (date.today() + timedelta(days=7)).isoformat()
    
    blocks_response = session.get(
        f'http://localhost:5002/admin/blocks?date_range_start={today}&date_range_end={next_week}'
    )
    
    if blocks_response.status_code != 200:
        print(f"✗ Failed to get blocks: {blocks_response.status_code}")
        return False
    
    blocks_data = blocks_response.json()
    blocks = blocks_data.get('blocks', [])
    
    # Find our test blocks
    test_blocks = [b for b in blocks if b.get('details') == test_identifier]
    
    if len(test_blocks) != 3:
        print(f"✗ Expected 3 test blocks, found {len(test_blocks)}")
        return False
    
    # Get the batch_id
    batch_id = test_blocks[0].get('batch_id')
    if not batch_id:
        print("✗ Test blocks have no batch_id")
        return False
    
    # Verify all test blocks have the same batch_id
    batch_ids = [b.get('batch_id') for b in test_blocks]
    if len(set(batch_ids)) != 1:
        print(f"✗ Test blocks have different batch_ids: {batch_ids}")
        return False
    
    print(f"✓ Found test blocks with batch_id: {batch_id}")
    
    # Delete the batch
    delete_response = session.delete(f'http://localhost:5002/admin/blocks/batch/{batch_id}')
    
    if delete_response.status_code != 200:
        print(f"✗ Failed to delete batch: {delete_response.status_code}")
        print(f"Response: {delete_response.text}")
        return False
    
    delete_data = delete_response.json()
    print(f"✓ Batch deleted: {delete_data.get('message', 'Success')}")
    
    # Verify all blocks in the batch are deleted
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
        for block in remaining_test_blocks:
            print(f"  Block {block['id']}: Court {block['court_number']}, batch_id: {block.get('batch_id', 'None')}")
        return False
    
    print("✓ All blocks in batch successfully deleted")
    
    return True

if __name__ == '__main__':
    print("Testing batch delete functionality...")
    success = test_batch_delete()
    
    if success:
        print("\n✓ Batch delete functionality working correctly!")
    else:
        print("\n✗ Batch delete functionality has issues.")