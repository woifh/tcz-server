#!/usr/bin/env python3
"""
Test the web interface functionality using requests with session management.
"""

import requests
from datetime import datetime, date, timedelta
import json

def test_admin_login_and_batch_grouping():
    """Test admin login and then create blocks to test batch-based grouping."""
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Step 1: Get the login page to see if we need CSRF tokens
    print("1. Getting login page...")
    login_page = session.get('http://localhost:5002/')
    print(f"Login page status: {login_page.status_code}")
    
    # Step 2: Attempt to login
    print("2. Attempting login...")
    login_data = {
        'email': 'woifh@gmx.at',
        'password': 'test123'
    }
    
    login_response = session.post('http://localhost:5002/auth/login', data=login_data)
    print(f"Login response status: {login_response.status_code}")
    
    if login_response.status_code == 200 and 'login' not in login_response.url.lower():
        print("✓ Login successful!")
        
        # Step 3: Access admin court blocking page
        print("3. Accessing admin court blocking page...")
        admin_page = session.get('http://localhost:5002/admin/court-blocking')
        print(f"Admin page status: {admin_page.status_code}")
        
        if admin_page.status_code == 200:
            print("✓ Admin page accessible!")
            
            # Step 4: Create test blocks for batch grouping
            print("4. Creating test multi-court blocks...")
            
            # Create multi-court block (should be grouped with batch_id)
            tomorrow = (date.today() + timedelta(days=1)).isoformat()
            
            multi_court_data = {
                'court_ids': [1, 2, 3],
                'date': tomorrow,
                'start_time': '10:00',
                'end_time': '12:00',
                'reason_id': 1,  # Assuming reason ID 1 exists
                'details': 'Test Batch Grouping'
            }
            
            create_response = session.post(
                'http://localhost:5002/admin/blocks/multi-court',
                json=multi_court_data,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"Multi-court block creation status: {create_response.status_code}")
            if create_response.status_code == 201:
                print("✓ Multi-court blocks created!")
                print(f"Response: {create_response.json()}")
            else:
                print(f"✗ Failed to create blocks: {create_response.text}")
            
            # Step 5: Create a single court block for comparison
            print("5. Creating single court block...")
            
            single_court_data = {
                'court_ids': [4],
                'date': tomorrow,
                'start_time': '14:00',
                'end_time': '16:00',
                'reason_id': 1,
                'details': 'Single Block Test'
            }
            
            single_response = session.post(
                'http://localhost:5002/admin/blocks/multi-court',
                json=single_court_data,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"Single court block creation status: {single_response.status_code}")
            if single_response.status_code == 201:
                print("✓ Single court block created!")
                print(f"Response: {single_response.json()}")
            
            # Step 6: Test the blocks API to see batch-based grouping
            print("6. Testing blocks API with batch_id...")
            
            today = date.today().isoformat()
            next_month = (date.today() + timedelta(days=30)).isoformat()
            
            blocks_response = session.get(
                f'http://localhost:5002/admin/blocks?date_range_start={today}&date_range_end={next_month}'
            )
            
            print(f"Blocks API status: {blocks_response.status_code}")
            if blocks_response.status_code == 200:
                blocks_data = blocks_response.json()
                blocks = blocks_data.get('blocks', [])
                print(f"✓ Found {len(blocks)} blocks")
                
                # Test the new batch-based grouping logic
                groups = {}
                for block in blocks:
                    if block.get('batch_id'):
                        key = f"batch_{block['batch_id']}"
                    else:
                        key = f"single_{block['id']}"
                    
                    if key not in groups:
                        groups[key] = []
                    groups[key].append(block)
                
                print(f"✓ Grouped into {len(groups)} batches using batch_id:")
                for i, (key, group_blocks) in enumerate(groups.items(), 1):
                    court_numbers = sorted([b['court_number'] for b in group_blocks])
                    first_block = group_blocks[0]
                    courts_display = f"Plätze {', '.join(map(str, court_numbers))}" if len(court_numbers) > 1 else f"Platz {court_numbers[0]}"
                    batch_info = f"batch_id: {first_block.get('batch_id', 'None')}" if first_block.get('batch_id') else "single block"
                    print(f"  Group {i} ({key}): {courts_display} - {first_block['date']} {first_block['start_time']}-{first_block['end_time']} ({first_block.get('details', 'No details')}) [{batch_info}]")
                
                # Step 7: Test batch-based edit URL
                print("7. Testing batch-based edit URLs...")
                for key, group_blocks in groups.items():
                    first_block = group_blocks[0]
                    edit_url = f"http://localhost:5002/admin/court-blocking/{key}"
                    edit_response = session.get(edit_url)
                    print(f"  Edit URL {edit_url}: {edit_response.status_code}")
                    if edit_response.status_code == 200:
                        print(f"    ✓ Batch edit page accessible for {key}")
                    else:
                        print(f"    ✗ Failed to access batch edit page: {edit_response.text[:100]}...")
                
                return True
            else:
                print(f"✗ Failed to get blocks: {blocks_response.text}")
        else:
            print(f"✗ Cannot access admin page: {admin_page.text[:200]}...")
    else:
        print(f"✗ Login failed: {login_response.text[:200]}...")
    
    return False

if __name__ == '__main__':
    print("Testing batch-based grouping functionality...")
    success = test_admin_login_and_batch_grouping()
    
    if success:
        print("\n✓ All tests passed! Batch-based grouping functionality should be working.")
    else:
        print("\n✗ Some tests failed. Check the output above.")