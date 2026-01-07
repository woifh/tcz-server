#!/usr/bin/env python3
"""
Test script to debug edit mode issues
"""
import requests
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
    
    if response.status_code == 200 and ('dashboard' in response.url or response.url.endswith('/')):
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

def test_edit_page_content(session, batch_id):
    """Test the edit page content to see what data is available"""
    print(f"🔍 Testing edit page for batch: {batch_id}")
    
    response = session.get(f"{BASE_URL}/admin/court-blocking/{batch_id}")
    
    if response.status_code == 200:
        content = response.text
        
        # Check for key elements
        if 'editBlockData' in content:
            print("✅ editBlockData found in page")
            
            # Extract the editBlockData
            start = content.find('window.editBlockData = {')
            if start != -1:
                end = content.find('};', start) + 2
                edit_data = content[start:end]
                print("📝 Edit data:")
                print(edit_data)
            
        else:
            print("❌ editBlockData not found in page")
        
        if 'data-edit-mode="true"' in content:
            print("✅ Form has edit-mode=true")
        else:
            print("❌ Form does not have edit-mode=true")
        
        if f'data-batch-id="{batch_id}"' in content:
            print("✅ Form has correct batch-id")
        else:
            print("❌ Form does not have correct batch-id")
            
        return True
    else:
        print(f"❌ Failed to access edit page: {response.status_code}")
        return False

def main():
    print("🐛 Debugging Edit Mode Issues")
    print("=" * 40)
    
    session = test_login()
    if not session:
        return
    
    print()
    
    batch_id = get_existing_batch(session)
    if not batch_id:
        print("❌ No existing batch found for testing")
        return
    
    print(f"📝 Using batch_id: {batch_id}")
    print()
    
    test_edit_page_content(session, batch_id)

if __name__ == "__main__":
    main()