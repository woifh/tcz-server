#!/usr/bin/env python3
"""
Test script to directly test batch update functionality
"""
import requests
import json
from datetime import datetime, date, timedelta

BASE_URL = "http://127.0.0.1:5001"

def test_login():
    """Test admin login"""
    session = requests.Session()
    
    login_data = {
        'email': 'woifh@gmx.at',
        'password': 'test123'
    }
    
    response = session.post(f"{BASE_URL}/auth/login", data=login_data)
    
    if response.status_code == 200:
        print("✅ Admin login successful")
        return session
    else:
        print(f"❌ Login failed: {response.status_code}")
        return None

def create_test_batch(session):
    """Create a test batch for updating"""
    # Get reasons
    response = session.get(f"{BASE_URL}/admin/block-reasons")
    reasons = response.json().get('reasons', [])
    reason_id = reasons[0]['id']
    
    # Create batch
    tomorrow = (date.today() + timedelta(days=3)).isoformat()
    
    block_data = {
        'court_ids': ['1', '2'],
        'date': tomorrow,
        'start_time': '10:00',
        'end_time': '12:00',
        'reason_id': reason_id,
        'details': 'Original batch for update test'
    }
    
    response = session.post(f"{BASE_URL}/admin/blocks/multi-court", json=block_data)
    
    if response.status_code == 201:
        print("✅ Created test batch")
        
        # Get the batch_id
        start_date = date.today().isoformat()
        end_date = (date.today() + timedelta(days=7)).isoformat()
        
        response = session.get(f"{BASE_URL}/admin/blocks", params={
            'date_range_start': start_date,
            'date_range_end': end_date
        })
        
        blocks = response.json().get('blocks', [])
        for block in blocks:
            if block.get('details') == 'Original batch for update test':
                return block['batch_id']
    
    return None

def test_batch_update_put_vs_post(session, batch_id):
    """Test both PUT and POST to see which one works"""
    print(f"🔧 Testing batch update for batch: {batch_id}")
    
    # Get reasons
    response = session.get(f"{BASE_URL}/admin/block-reasons")
    reasons = response.json().get('reasons', [])
    reason_id = reasons[1]['id'] if len(reasons) > 1 else reasons[0]['id']
    
    update_data = {
        'court_ids': ['3', '4', '5'],
        'date': (date.today() + timedelta(days=3)).isoformat(),
        'start_time': '14:00',
        'end_time': '16:00',
        'reason_id': reason_id,
        'details': 'Updated via PUT test'
    }
    
    # Test PUT request (correct method)
    print("📤 Testing PUT request...")
    response = session.put(f"{BASE_URL}/admin/blocks/batch/{batch_id}", json=update_data)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ PUT request successful: {data.get('message')}")
        print(f"   Courts updated: {data.get('courts_updated', 0)}")
        print(f"   Courts added: {data.get('courts_added', 0)}")
        print(f"   Courts removed: {data.get('courts_removed', 0)}")
    else:
        print(f"❌ PUT request failed: {response.status_code}")
        if response.headers.get('content-type', '').startswith('application/json'):
            error_data = response.json()
            print(f"   Error: {error_data.get('error', 'Unknown error')}")
    
    print()
    
    # Test POST request (incorrect method - should fail or create new)
    print("📤 Testing POST request...")
    update_data['details'] = 'Updated via POST test'
    response = session.post(f"{BASE_URL}/admin/blocks/batch/{batch_id}", json=update_data)
    
    print(f"📊 POST response status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"⚠️  POST request unexpectedly successful: {data.get('message')}")
    elif response.status_code == 405:
        print("✅ POST request correctly rejected (Method Not Allowed)")
    else:
        print(f"❓ POST request returned: {response.status_code}")
        if response.headers.get('content-type', '').startswith('application/json'):
            error_data = response.json()
            print(f"   Error: {error_data.get('error', 'Unknown error')}")

def verify_update_results(session, batch_id):
    """Verify the update results"""
    print(f"🔍 Verifying update results for batch: {batch_id}")
    
    start_date = date.today().isoformat()
    end_date = (date.today() + timedelta(days=7)).isoformat()
    
    response = session.get(f"{BASE_URL}/admin/blocks", params={
        'date_range_start': start_date,
        'date_range_end': end_date
    })
    
    if response.status_code == 200:
        blocks = response.json().get('blocks', [])
        batch_blocks = [b for b in blocks if b.get('batch_id') == batch_id]
        
        if batch_blocks:
            print(f"✅ Found {len(batch_blocks)} blocks in batch")
            first_block = batch_blocks[0]
            court_numbers = sorted([b.get('court_number', b.get('court_id')) for b in batch_blocks])
            
            print(f"   Courts: {court_numbers}")
            print(f"   Time: {first_block.get('start_time')} - {first_block.get('end_time')}")
            print(f"   Details: {first_block.get('details')}")
            
            return True
        else:
            print("❌ No blocks found for the batch")
            return False
    else:
        print(f"❌ Failed to get blocks: {response.status_code}")
        return False

def main():
    print("🧪 Testing Direct Batch Update (PUT vs POST)")
    print("=" * 50)
    
    session = test_login()
    if not session:
        return
    
    print()
    
    batch_id = create_test_batch(session)
    if not batch_id:
        print("❌ Failed to create test batch")
        return
    
    print(f"📝 Using batch_id: {batch_id}")
    print()
    
    test_batch_update_put_vs_post(session, batch_id)
    print()
    
    verify_update_results(session, batch_id)

if __name__ == "__main__":
    main()