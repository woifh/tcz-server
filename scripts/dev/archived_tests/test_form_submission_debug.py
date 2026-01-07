#!/usr/bin/env python3
"""
Test script to debug form submission issues by monitoring server requests
"""
import requests
import time
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

def get_existing_batch(session):
    """Get an existing batch for testing"""
    start_date = date.today().isoformat()
    end_date = (date.today() + timedelta(days=7)).isoformat()
    
    response = session.get(f"{BASE_URL}/admin/blocks", params={
        'date_range_start': start_date,
        'date_range_end': end_date
    })
    
    if response.status_code == 200:
        blocks = response.json().get('blocks', [])
        for block in blocks:
            if block.get('batch_id'):
                return block['batch_id']
    
    return None

def simulate_form_submission_via_post(session, batch_id):
    """Simulate what happens when the form submits via POST (the current problem)"""
    print(f"🔍 Simulating form POST submission for batch: {batch_id}")
    
    # This simulates what the HTML form would do if it submits via POST
    # to the multi-court endpoint (which is what's happening incorrectly)
    
    form_data = {
        'court_ids': ['2', '3'],
        'date': (date.today() + timedelta(days=1)).isoformat(),
        'start_time': '15:00',
        'end_time': '17:00',
        'reason_id': '1',
        'details': 'Form POST submission test'
    }
    
    # This is what's happening incorrectly - POST to multi-court instead of PUT to batch
    response = session.post(f"{BASE_URL}/admin/blocks/multi-court", json=form_data)
    
    if response.status_code == 201:
        print("❌ Form incorrectly created NEW blocks via POST (this is the problem!)")
        data = response.json()
        print(f"   Message: {data.get('message')}")
        return True
    else:
        print(f"❓ POST request failed: {response.status_code}")
        return False

def test_correct_put_submission(session, batch_id):
    """Test the correct PUT submission that should happen"""
    print(f"✅ Testing correct PUT submission for batch: {batch_id}")
    
    form_data = {
        'court_ids': ['4', '5'],
        'date': (date.today() + timedelta(days=1)).isoformat(),
        'start_time': '15:00',
        'end_time': '17:00',
        'reason_id': '1',
        'details': 'Correct PUT submission test'
    }
    
    # This is what SHOULD happen - PUT to batch endpoint
    response = session.put(f"{BASE_URL}/admin/blocks/batch/{batch_id}", json=form_data)
    
    if response.status_code == 200:
        print("✅ Correct PUT request updated existing batch")
        data = response.json()
        print(f"   Message: {data.get('message')}")
        return True
    else:
        print(f"❌ PUT request failed: {response.status_code}")
        return False

def check_what_blocks_exist(session):
    """Check what blocks exist to see the difference"""
    print("📊 Checking existing blocks...")
    
    start_date = date.today().isoformat()
    end_date = (date.today() + timedelta(days=7)).isoformat()
    
    response = session.get(f"{BASE_URL}/admin/blocks", params={
        'date_range_start': start_date,
        'date_range_end': end_date
    })
    
    if response.status_code == 200:
        blocks = response.json().get('blocks', [])
        
        # Group by batch_id
        batches = {}
        for block in blocks:
            batch_id = block.get('batch_id', 'None')
            if batch_id not in batches:
                batches[batch_id] = []
            batches[batch_id].append(block)
        
        for batch_id, batch_blocks in batches.items():
            if len(batch_blocks) > 0:
                first_block = batch_blocks[0]
                court_numbers = [b.get('court_number', b.get('court_id')) for b in batch_blocks]
                print(f"   Batch {batch_id}: Courts {court_numbers} - {first_block.get('details', 'No details')}")
        
        return blocks
    else:
        print(f"❌ Failed to get blocks: {response.status_code}")
        return []

def main():
    print("🐛 Debugging Form Submission Issues")
    print("=" * 50)
    
    session = test_login()
    if not session:
        return
    
    print()
    
    # Check initial state
    print("📋 Initial state:")
    initial_blocks = check_what_blocks_exist(session)
    print()
    
    # Get an existing batch
    batch_id = get_existing_batch(session)
    if not batch_id:
        print("❌ No existing batch found for testing")
        return
    
    print(f"📝 Using batch_id: {batch_id}")
    print()
    
    # Simulate the incorrect POST submission (what's happening now)
    print("🚨 Simulating INCORRECT behavior (POST creating new blocks):")
    simulate_form_submission_via_post(session, batch_id)
    print()
    
    # Show what happened
    print("📋 After incorrect POST:")
    check_what_blocks_exist(session)
    print()
    
    # Test the correct PUT submission
    print("✅ Testing CORRECT behavior (PUT updating existing batch):")
    test_correct_put_submission(session, batch_id)
    print()
    
    # Show final state
    print("📋 After correct PUT:")
    check_what_blocks_exist(session)
    
    print()
    print("🎯 CONCLUSION:")
    print("   - The form is currently doing POST to /admin/blocks/multi-court (creates new)")
    print("   - It should be doing PUT to /admin/blocks/batch/{batch_id} (updates existing)")

if __name__ == "__main__":
    main()