#!/usr/bin/env python3

import requests
import sys

def test_batch_id_in_edit_page():
    """Test if the edit page now has the correct batch_id in the template."""
    
    # First, create a test batch
    print("🔧 Creating test batch...")
    
    session = requests.Session()
    
    # Login as admin
    login_data = {
        'email': 'admin@example.com',
        'password': 'admin123'
    }
    
    login_response = session.post('http://localhost:5001/login', data=login_data)
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False
    
    # Create a multi-court block
    block_data = {
        'court_ids': [1, 2, 3],
        'date': '2026-01-04',
        'start_time': '10:00',
        'end_time': '12:00',
        'reason_id': 1,
        'details': 'Test batch ID fix'
    }
    
    create_response = session.post('http://localhost:5001/admin/blocks/multi-court', json=block_data)
    if create_response.status_code != 201:
        print(f"❌ Block creation failed: {create_response.status_code}")
        print(f"Response: {create_response.text}")
        return False
    
    print("✅ Test batch created successfully")
    
    # Get the created blocks to find the batch_id
    blocks_response = session.get('http://localhost:5001/admin/blocks?date=2026-01-04')
    if blocks_response.status_code != 200:
        print(f"❌ Failed to get blocks: {blocks_response.status_code}")
        return False
    
    blocks_data = blocks_response.json()
    test_blocks = [b for b in blocks_data['blocks'] if b['details'] == 'Test batch ID fix']
    
    if not test_blocks:
        print("❌ No test blocks found")
        return False
    
    batch_id = test_blocks[0]['batch_id']
    print(f"📋 Found batch_id: {batch_id}")
    
    # Now test the edit page
    print(f"🔍 Testing edit page for batch: {batch_id}")
    
    edit_url = f'http://localhost:5001/admin/court-blocking/{batch_id}'
    edit_response = session.get(edit_url)
    
    if edit_response.status_code != 200:
        print(f"❌ Edit page failed: {edit_response.status_code}")
        return False
    
    html_content = edit_response.text
    
    # Check if the data-batch-id attribute has the correct value
    if f'data-batch-id="{batch_id}"' in html_content:
        print(f"✅ data-batch-id attribute is correctly set to: {batch_id}")
    else:
        print(f"❌ data-batch-id attribute is NOT correctly set")
        print("Looking for data-batch-id in HTML...")
        
        # Find the data-batch-id line
        lines = html_content.split('\n')
        for i, line in enumerate(lines):
            if 'data-batch-id=' in line:
                print(f"Line {i+1}: {line.strip()}")
    
    # Check if window.editBlockData has the correct batch_id
    if f"batch_id: '{batch_id}'" in html_content:
        print(f"✅ window.editBlockData.batch_id is correctly set to: {batch_id}")
    else:
        print(f"❌ window.editBlockData.batch_id is NOT correctly set")
        print("Looking for batch_id in JavaScript...")
        
        # Find the JavaScript section
        lines = html_content.split('\n')
        in_script = False
        for i, line in enumerate(lines):
            if 'window.editBlockData' in line:
                in_script = True
            if in_script and 'batch_id:' in line:
                print(f"Line {i+1}: {line.strip()}")
                break
    
    # Clean up - delete the test blocks
    print("🧹 Cleaning up test blocks...")
    delete_response = session.delete(f'http://localhost:5001/admin/blocks/batch/{batch_id}')
    if delete_response.status_code == 200:
        print("✅ Test blocks cleaned up")
    else:
        print(f"⚠️ Failed to clean up test blocks: {delete_response.status_code}")
    
    return True

if __name__ == '__main__':
    success = test_batch_id_in_edit_page()
    sys.exit(0 if success else 1)