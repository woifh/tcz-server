#!/usr/bin/env python3
"""
Test script to verify the complete batch edit workflow
"""
import requests
import json
from datetime import datetime, date, timedelta

BASE_URL = "http://127.0.0.1:5001"

def test_login():
    """Test admin login"""
    session = requests.Session()
    
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

def test_create_batch_for_editing(session):
    """Create a batch specifically for testing edit functionality"""
    # Get reasons first
    response = session.get(f"{BASE_URL}/admin/block-reasons")
    if response.status_code != 200:
        print("❌ Failed to get reasons")
        return None
    
    reasons = response.json().get('reasons', [])
    if not reasons:
        print("❌ No reasons available")
        return None
    
    reason_id = reasons[0]['id']
    
    # Create block for tomorrow
    tomorrow = (date.today() + timedelta(days=2)).isoformat()
    
    block_data = {
        'court_ids': ['1', '3', '5'],  # Courts 1, 3, 5
        'date': tomorrow,
        'start_time': '09:00',
        'end_time': '11:00',
        'reason_id': reason_id,
        'details': 'Original test blocking for edit'
    }
    
    response = session.post(f"{BASE_URL}/admin/blocks/multi-court", json=block_data)
    
    if response.status_code == 201:
        print("✅ Created test batch for editing")
        
        # Get the created blocks to find the batch_id
        start_date = date.today().isoformat()
        end_date = (date.today() + timedelta(days=7)).isoformat()
        
        response = session.get(f"{BASE_URL}/admin/blocks", params={
            'date_range_start': start_date,
            'date_range_end': end_date
        })
        
        if response.status_code == 200:
            blocks = response.json().get('blocks', [])
            # Find our newly created batch
            for block in blocks:
                if (block.get('details') == 'Original test blocking for edit' and 
                    block.get('batch_id')):
                    return block['batch_id']
        
        print("❌ Could not find batch_id of created blocks")
        return None
    else:
        print(f"❌ Failed to create test batch: {response.status_code}")
        return None

def test_batch_edit_via_api(session, batch_id):
    """Test editing the batch via direct API call"""
    print(f"🔧 Testing batch edit via API for batch: {batch_id}")
    
    # Get reasons for the update
    response = session.get(f"{BASE_URL}/admin/block-reasons")
    reasons = response.json().get('reasons', [])
    reason_id = reasons[1]['id'] if len(reasons) > 1 else reasons[0]['id']  # Use different reason
    
    # Update the batch - change courts, time, and reason
    update_data = {
        'court_ids': ['2', '4', '6'],  # Different courts
        'date': (date.today() + timedelta(days=2)).isoformat(),
        'start_time': '13:00',  # Different time
        'end_time': '15:00',
        'reason_id': reason_id,
        'details': 'Updated via API test'
    }
    
    response = session.put(f"{BASE_URL}/admin/blocks/batch/{batch_id}", json=update_data)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Batch updated via API: {data.get('message')}")
        print(f"   Courts updated: {data.get('courts_updated', 0)}")
        print(f"   Courts added: {data.get('courts_added', 0)}")
        print(f"   Courts removed: {data.get('courts_removed', 0)}")
        return True
    else:
        print(f"❌ Failed to update batch via API: {response.status_code}")
        if response.headers.get('content-type', '').startswith('application/json'):
            error_data = response.json()
            print(f"   Error: {error_data.get('error', 'Unknown error')}")
        return False

def test_batch_edit_page_access(session, batch_id):
    """Test accessing the batch edit page"""
    print(f"🌐 Testing batch edit page access for batch: {batch_id}")
    
    response = session.get(f"{BASE_URL}/admin/court-blocking/{batch_id}")
    
    if response.status_code == 200:
        print("✅ Batch edit page accessible")
        
        # Check if the page contains the expected edit data
        content = response.text
        if 'editBlockData' in content and batch_id in content:
            print("✅ Edit data properly embedded in page")
            return True
        else:
            print("❌ Edit data not found in page")
            return False
    else:
        print(f"❌ Failed to access batch edit page: {response.status_code}")
        return False

def verify_batch_changes(session, batch_id):
    """Verify that the batch changes were applied correctly"""
    print(f"🔍 Verifying batch changes for batch: {batch_id}")
    
    # Get blocks to verify changes
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
            print(f"✅ Found {len(batch_blocks)} blocks in updated batch")
            
            # Verify the changes
            first_block = batch_blocks[0]
            court_numbers = sorted([b.get('court_number', b.get('court_id')) for b in batch_blocks])
            
            print(f"   Courts: {court_numbers}")
            print(f"   Time: {first_block.get('start_time')} - {first_block.get('end_time')}")
            print(f"   Reason: {first_block.get('reason_name')}")
            print(f"   Details: {first_block.get('details')}")
            
            # Check if changes match what we expected
            expected_courts = [2, 4, 6]
            if court_numbers == expected_courts:
                print("✅ Court changes applied correctly")
            else:
                print(f"❌ Court changes incorrect. Expected {expected_courts}, got {court_numbers}")
            
            if first_block.get('start_time') == '13:00' and first_block.get('end_time') == '15:00':
                print("✅ Time changes applied correctly")
            else:
                print(f"❌ Time changes incorrect")
            
            if first_block.get('details') == 'Updated via API test':
                print("✅ Details changes applied correctly")
            else:
                print(f"❌ Details changes incorrect")
            
            return True
        else:
            print("❌ No blocks found for the batch")
            return False
    else:
        print(f"❌ Failed to get blocks for verification: {response.status_code}")
        return False

def main():
    print("🧪 Testing Complete Batch Edit Workflow")
    print("=" * 50)
    
    # Test login
    session = test_login()
    if not session:
        return
    
    print()
    
    # Create a batch for testing
    batch_id = test_create_batch_for_editing(session)
    if not batch_id:
        return
    
    print(f"📝 Using batch_id: {batch_id}")
    print()
    
    # Test batch edit via API
    if not test_batch_edit_via_api(session, batch_id):
        return
    
    print()
    
    # Test batch edit page access
    test_batch_edit_page_access(session, batch_id)
    print()
    
    # Verify the changes were applied
    verify_batch_changes(session, batch_id)
    print()
    
    print("✅ Complete batch edit workflow test completed!")

if __name__ == "__main__":
    main()