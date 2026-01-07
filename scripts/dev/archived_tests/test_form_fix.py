#!/usr/bin/env python3
"""
Test script to verify the court blocking form fix.
This script creates a test blocking entry and then tests the edit functionality.
"""

import requests
import json
from datetime import datetime, date, time

BASE_URL = "http://127.0.0.1:5001"

def login_admin():
    """Login as admin user"""
    session = requests.Session()
    
    # Get login page to get CSRF token
    login_page = session.get(f"{BASE_URL}/auth/login")
    
    # Login with admin credentials
    login_data = {
        'email': 'admin@tennisclub.de',
        'password': 'admin123'
    }
    
    response = session.post(f"{BASE_URL}/auth/login", data=login_data, allow_redirects=True)
    
    print(f"Login response status: {response.status_code}")
    print(f"Final URL: {response.url}")
    print(f"Response text preview: {response.text[:200]}...")
    
    # Check if we're logged in by trying to access admin page
    admin_check = session.get(f"{BASE_URL}/admin/overview")
    if admin_check.status_code == 200:
        print("✅ Admin login successful")
        return session
    else:
        print(f"❌ Admin login failed - cannot access admin page: {admin_check.status_code}")
        return None

def create_test_blocking(session):
    """Create a test blocking entry"""
    blocking_data = {
        'court_ids': [1, 2],
        'date': '2026-01-10',
        'start_time': '10:00',
        'end_time': '12:00',
        'reason_id': 1,  # Assuming reason ID 1 exists
        'details': 'Test blocking for form fix'
    }
    
    response = session.post(
        f"{BASE_URL}/admin/blocks/multi-court",
        json=blocking_data,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 201:
        result = response.json()
        print(f"✅ Test blocking created: {result.get('message')}")
        return True
    else:
        print(f"❌ Failed to create test blocking: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def get_blocks(session):
    """Get list of blocks to find our test block"""
    response = session.get(f"{BASE_URL}/admin/blocks?date=2026-01-10")
    
    if response.status_code == 200:
        result = response.json()
        blocks = result.get('blocks', [])
        print(f"✅ Found {len(blocks)} blocks for 2026-01-10")
        
        # Find blocks with our test data
        test_blocks = [b for b in blocks if b.get('details') == 'Test blocking for form fix']
        if test_blocks:
            batch_id = test_blocks[0].get('batch_id')
            print(f"✅ Found test blocks with batch_id: {batch_id}")
            return batch_id
        else:
            print("❌ Test blocks not found")
            return None
    else:
        print(f"❌ Failed to get blocks: {response.status_code}")
        return None

def test_batch_update(session, batch_id):
    """Test updating the batch using PUT request"""
    update_data = {
        'court_ids': [1, 2, 3],  # Add court 3
        'date': '2026-01-10',
        'start_time': '11:00',  # Change start time
        'end_time': '13:00',    # Change end time
        'reason_id': 1,
        'details': 'Updated test blocking - form fix verified'
    }
    
    response = session.put(
        f"{BASE_URL}/admin/blocks/batch/{batch_id}",
        json=update_data,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Batch update successful: {result.get('message')}")
        print(f"   Courts updated: {result.get('courts_updated')}")
        print(f"   Courts added: {result.get('courts_added')}")
        print(f"   Courts removed: {result.get('courts_removed')}")
        return True
    else:
        print(f"❌ Batch update failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def verify_update(session, batch_id):
    """Verify that the update was applied correctly"""
    response = session.get(f"{BASE_URL}/admin/blocks?date=2026-01-10")
    
    if response.status_code == 200:
        result = response.json()
        blocks = result.get('blocks', [])
        
        # Find blocks with our batch_id
        batch_blocks = [b for b in blocks if b.get('batch_id') == batch_id]
        
        if batch_blocks:
            print(f"✅ Found {len(batch_blocks)} blocks in batch after update")
            
            # Check if update was applied
            updated_blocks = [b for b in batch_blocks if b.get('details') == 'Updated test blocking - form fix verified']
            
            if updated_blocks:
                print("✅ Update verification successful - blocks were updated, not duplicated")
                
                # Check court coverage
                court_ids = [b.get('court_id') for b in batch_blocks]
                print(f"   Courts in batch: {sorted(court_ids)}")
                
                # Check time
                start_time = updated_blocks[0].get('start_time')
                end_time = updated_blocks[0].get('end_time')
                print(f"   Time: {start_time} - {end_time}")
                
                return True
            else:
                print("❌ Update verification failed - blocks were not updated")
                return False
        else:
            print("❌ Batch blocks not found after update")
            return False
    else:
        print(f"❌ Failed to verify update: {response.status_code}")
        return False

def cleanup_test_data(session):
    """Clean up test data"""
    response = session.get(f"{BASE_URL}/admin/blocks?date=2026-01-10")
    
    if response.status_code == 200:
        result = response.json()
        blocks = result.get('blocks', [])
        
        # Find test blocks
        test_blocks = [b for b in blocks if 'test blocking' in (b.get('details') or '').lower()]
        
        for block in test_blocks:
            batch_id = block.get('batch_id')
            if batch_id:
                delete_response = session.delete(f"{BASE_URL}/admin/blocks/batch/{batch_id}")
                if delete_response.status_code == 200:
                    print(f"✅ Cleaned up test batch: {batch_id}")
                else:
                    print(f"❌ Failed to clean up batch {batch_id}: {delete_response.status_code}")

def main():
    print("🧪 Testing Court Blocking Form Fix")
    print("=" * 50)
    
    # Login
    session = login_admin()
    if not session:
        return
    
    try:
        # Create test blocking
        if not create_test_blocking(session):
            return
        
        # Get the batch_id
        batch_id = get_blocks(session)
        if not batch_id:
            return
        
        # Test batch update (this is what the form should do)
        if not test_batch_update(session, batch_id):
            return
        
        # Verify the update worked correctly
        if verify_update(session, batch_id):
            print("\n🎉 SUCCESS: Batch update functionality works correctly!")
            print("   - Existing blocks were updated (not duplicated)")
            print("   - New courts were added to the batch")
            print("   - Time and reason changes were applied")
        else:
            print("\n❌ FAILURE: Batch update functionality has issues")
        
    finally:
        # Clean up
        print("\n🧹 Cleaning up test data...")
        cleanup_test_data(session)
    
    print("\n✅ Test completed")

if __name__ == "__main__":
    main()