#!/usr/bin/env python3
"""
Test script for court blocking functionality.
Tests the admin court blocking form and API endpoints.
"""

import requests
import json
import os
from datetime import datetime, date, timedelta

# Set the correct database URL
os.environ['DATABASE_URL'] = 'sqlite:////Users/woifh/tcz/instance/tennis_club.db'

# Test configuration
BASE_URL = 'http://localhost:5001'
ADMIN_EMAIL = 'testadmin@test.com'  # Test admin user
ADMIN_PASSWORD = 'admin123'  # Known password

def test_login():
    """Test admin login functionality."""
    print("Testing admin login...")
    
    session = requests.Session()
    
    # Get login page to get CSRF token if needed
    login_page = session.get(f'{BASE_URL}/auth/login')
    print(f"Login page status: {login_page.status_code}")
    
    # Attempt login
    login_data = {
        'email': ADMIN_EMAIL,
        'password': ADMIN_PASSWORD
    }
    
    login_response = session.post(f'{BASE_URL}/auth/login', data=login_data)
    print(f"Login response status: {login_response.status_code}")
    
    if login_response.status_code == 200 and 'dashboard' in login_response.url:
        print("✅ Login successful!")
        return session
    else:
        print("❌ Login failed!")
        print(f"Response URL: {login_response.url}")
        return None

def test_block_reasons_api(session):
    """Test the block reasons API endpoint."""
    print("\nTesting block reasons API...")
    
    response = session.get(f'{BASE_URL}/admin/block-reasons')
    print(f"Block reasons API status: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            reasons = data.get('reasons', [])
            print(f"✅ Found {len(reasons)} block reasons:")
            for reason in reasons:
                print(f"  - {reason['name']} (ID: {reason['id']}, Active: {reason['is_active']})")
            return reasons
        except json.JSONDecodeError:
            print("❌ Invalid JSON response")
            return []
    else:
        print(f"❌ API request failed with status {response.status_code}")
        return []

def test_court_blocking_page(session):
    """Test access to the court blocking page."""
    print("\nTesting court blocking page access...")
    
    response = session.get(f'{BASE_URL}/admin/court-blocking')
    print(f"Court blocking page status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Court blocking page accessible")
        # Check if the page contains expected elements
        content = response.text
        if 'multi-court-form' in content:
            print("✅ Multi-court form found in page")
        else:
            print("❌ Multi-court form not found in page")
        
        if 'blocks-list' in content:
            print("✅ Blocks list container found in page")
        else:
            print("❌ Blocks list container not found in page")
            
        return True
    else:
        print(f"❌ Court blocking page not accessible: {response.status_code}")
        return False

def test_create_block_api(session, reasons):
    """Test creating a block via API."""
    print("\nTesting block creation API...")
    
    if not reasons:
        print("❌ No block reasons available for testing")
        return False
    
    # Use the first available reason
    reason_id = reasons[0]['id']
    
    # Create test block data
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    block_data = {
        'court_ids': [1, 2],  # Block courts 1 and 2
        'date': tomorrow,
        'start_time': '10:00',
        'end_time': '12:00',
        'reason_id': reason_id,
        'details': 'Test block creation'
    }
    
    print(f"Creating block: {block_data}")
    
    response = session.post(
        f'{BASE_URL}/admin/blocks/multi-court',
        json=block_data,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Block creation API status: {response.status_code}")
    
    if response.status_code == 201:
        try:
            data = response.json()
            print(f"✅ Block created successfully: {data.get('message')}")
            print(f"   Blocks created: {data.get('blocks_created')}")
            return True
        except json.JSONDecodeError:
            print("❌ Invalid JSON response")
            return False
    else:
        try:
            error_data = response.json()
            print(f"❌ Block creation failed: {error_data.get('error', 'Unknown error')}")
        except json.JSONDecodeError:
            print(f"❌ Block creation failed with status {response.status_code}")
        return False

def test_list_blocks_api(session):
    """Test listing blocks via API."""
    print("\nTesting blocks listing API...")
    
    # Get blocks for the next 30 days
    today = date.today().isoformat()
    next_month = (date.today() + timedelta(days=30)).isoformat()
    
    params = {
        'date_range_start': today,
        'date_range_end': next_month
    }
    
    response = session.get(f'{BASE_URL}/admin/blocks', params=params)
    print(f"Blocks listing API status: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            blocks = data.get('blocks', [])
            print(f"✅ Found {len(blocks)} blocks:")
            for block in blocks[:5]:  # Show first 5 blocks
                print(f"  - Court {block['court_number']}: {block['date']} {block['start_time']}-{block['end_time']} ({block['reason_name']})")
            return blocks
        except json.JSONDecodeError:
            print("❌ Invalid JSON response")
            return []
    else:
        print(f"❌ Blocks listing failed with status {response.status_code}")
        return []

def main():
    """Run all tests."""
    print("🧪 Testing Court Blocking Functionality")
    print("=" * 50)
    
    # Test login
    session = test_login()
    if not session:
        print("\n❌ Cannot proceed without successful login")
        return
    
    # Test block reasons API
    reasons = test_block_reasons_api(session)
    
    # Test court blocking page
    page_accessible = test_court_blocking_page(session)
    
    # Test block creation API
    if reasons:
        block_created = test_create_block_api(session, reasons)
    else:
        print("\n⚠️  Skipping block creation test - no reasons available")
        block_created = False
    
    # Test blocks listing API
    blocks = test_list_blocks_api(session)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"✅ Login: {'Success' if session else 'Failed'}")
    print(f"✅ Block Reasons API: {'Success' if reasons else 'Failed'}")
    print(f"✅ Court Blocking Page: {'Success' if page_accessible else 'Failed'}")
    print(f"✅ Block Creation API: {'Success' if block_created else 'Failed'}")
    print(f"✅ Blocks Listing API: {'Success' if blocks else 'Failed'}")
    
    if all([session, reasons, page_accessible, blocks]):
        print("\n🎉 All core functionality tests passed!")
        print("\nNext steps:")
        print("1. Open http://localhost:5001/admin/court-blocking in your browser")
        print("2. Log in with admin credentials")
        print("3. Test the form manually:")
        print("   - Select one or more courts")
        print("   - Choose a date")
        print("   - Set start/end times")
        print("   - Select a reason")
        print("   - Submit the form")
        print("4. Verify the block appears in the 'Kommende Sperrungen' list")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

if __name__ == '__main__':
    main()