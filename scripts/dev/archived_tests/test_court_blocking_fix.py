#!/usr/bin/env python3
"""
Test script to verify court blocking functionality fixes
"""
import requests
import json
from datetime import datetime, date, timedelta

BASE_URL = "http://127.0.0.1:5001"

def test_login():
    """Test admin login"""
    session = requests.Session()
    
    # Get login page first to get CSRF token if needed
    login_page = session.get(f"{BASE_URL}/auth/login")
    
    # Login with admin credentials
    login_data = {
        'email': 'woifh@gmx.at',
        'password': 'test123'
    }
    
    response = session.post(f"{BASE_URL}/auth/login", data=login_data)
    
    if response.status_code == 200 and ('dashboard' in response.url or response.url.endswith('/')):
        print("✅ Admin login successful")
        return session
    else:
        print(f"❌ Login failed: {response.status_code}, URL: {response.url}")
        return None

def test_block_reasons_api(session):
    """Test block reasons API"""
    response = session.get(f"{BASE_URL}/admin/block-reasons")
    
    if response.status_code == 200:
        data = response.json()
        reasons = data.get('reasons', [])
        print(f"✅ Block reasons loaded: {len(reasons)} reasons found")
        for reason in reasons[:3]:  # Show first 3
            print(f"   - {reason['name']} (ID: {reason['id']})")
        return reasons
    else:
        print(f"❌ Failed to load block reasons: {response.status_code}")
        return []

def test_create_block(session, reasons):
    """Test creating a multi-court block"""
    if not reasons:
        print("❌ No reasons available for testing")
        return
    
    # Use first available reason
    reason_id = reasons[0]['id']
    
    # Create block for tomorrow
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    
    block_data = {
        'court_ids': ['1', '2'],  # Courts 1 and 2
        'date': tomorrow,
        'start_time': '10:00',
        'end_time': '12:00',
        'reason_id': reason_id,
        'details': 'Test blocking'
    }
    
    response = session.post(f"{BASE_URL}/admin/blocks/multi-court", json=block_data)
    
    if response.status_code == 201:
        data = response.json()
        print(f"✅ Multi-court block created: {data.get('message')}")
        return True
    else:
        print(f"❌ Failed to create block: {response.status_code}")
        if response.headers.get('content-type', '').startswith('application/json'):
            error_data = response.json()
            print(f"   Error: {error_data.get('error', 'Unknown error')}")
        return False

def test_list_blocks(session):
    """Test listing blocks"""
    # Get blocks for the next 7 days
    start_date = date.today().isoformat()
    end_date = (date.today() + timedelta(days=7)).isoformat()
    
    response = session.get(f"{BASE_URL}/admin/blocks", params={
        'date_range_start': start_date,
        'date_range_end': end_date
    })
    
    if response.status_code == 200:
        data = response.json()
        blocks = data.get('blocks', [])
        print(f"✅ Blocks loaded: {len(blocks)} blocks found")
        
        # Group by batch_id to show batches
        batches = {}
        for block in blocks:
            batch_id = block.get('batch_id')
            if batch_id not in batches:
                batches[batch_id] = []
            batches[batch_id].append(block)
        
        for batch_id, batch_blocks in batches.items():
            court_numbers = [b.get('court_number', b.get('court_id', '?')) for b in batch_blocks]
            first_block = batch_blocks[0]
            print(f"   Batch {batch_id}: Courts {', '.join(map(str, court_numbers))} - {first_block.get('reason_name', 'Unknown')} on {first_block.get('date')}")
        
        return blocks
    else:
        print(f"❌ Failed to load blocks: {response.status_code}")
        return []

def test_update_batch(session, blocks):
    """Test updating a batch of blocks"""
    if not blocks:
        print("❌ No blocks available for testing batch update")
        return
    
    # Find a batch to update
    batch_id = None
    for block in blocks:
        if block.get('batch_id'):
            batch_id = block['batch_id']
            break
    
    if not batch_id:
        print("❌ No batch_id found in blocks for testing")
        return
    
    # Update the batch - change time and add/remove courts
    update_data = {
        'court_ids': ['2', '3', '4'],  # Different courts
        'date': (date.today() + timedelta(days=1)).isoformat(),
        'start_time': '14:00',  # Different time
        'end_time': '16:00',
        'reason_id': blocks[0].get('reason_id'),  # Keep same reason
        'details': 'Updated test blocking'
    }
    
    response = session.put(f"{BASE_URL}/admin/blocks/batch/{batch_id}", json=update_data)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Batch updated: {data.get('message')}")
        print(f"   Courts updated: {data.get('courts_updated', 0)}")
        print(f"   Courts added: {data.get('courts_added', 0)}")
        print(f"   Courts removed: {data.get('courts_removed', 0)}")
        return True
    else:
        print(f"❌ Failed to update batch: {response.status_code}")
        if response.headers.get('content-type', '').startswith('application/json'):
            error_data = response.json()
            print(f"   Error: {error_data.get('error', 'Unknown error')}")
        return False
    print("🧪 Testing Court Blocking Functionality Fixes")
    print("=" * 50)
    
    # Test login
    session = test_login()
    if not session:
        return
    
    print()
    
    # Test block reasons API
    reasons = test_block_reasons_api(session)
    print()
    
    # Test creating a block
    test_create_block(session, reasons)
    print()
    
    # Test listing blocks
    test_list_blocks(session)
    print()
    
def main():
    print("🧪 Testing Court Blocking Functionality Fixes")
    print("=" * 50)
    
    # Test login
    session = test_login()
    if not session:
        return
    
    print()
    
    # Test block reasons API
    reasons = test_block_reasons_api(session)
    print()
    
    # Test creating a block
    test_create_block(session, reasons)
    print()
    
    # Test listing blocks
    blocks = test_list_blocks(session)
    print()
    
    # Test updating a batch
    test_update_batch(session, blocks)
    print()
    
    print("✅ All tests completed!")

if __name__ == "__main__":
    main()