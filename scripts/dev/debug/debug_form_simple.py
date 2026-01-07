#!/usr/bin/env python3
"""
Simple debug script to test form data attributes
"""

import requests
import re

def test_edit_page_data_attributes():
    """Test that the edit page renders correct data attributes"""
    
    # Test with a known batch ID
    batch_id = "1d40fb5c-500c-4127-9c4a-05d9f53fe47f"
    edit_url = f"http://127.0.0.1:5001/admin/court-blocking/{batch_id}"
    
    print(f"🔍 Testing edit page: {edit_url}")
    
    try:
        response = requests.get(edit_url)
        if response.status_code != 200:
            print(f"❌ Failed to load page: {response.status_code}")
            return False
            
        html = response.text
        
        # Extract form data attributes using regex
        edit_mode_match = re.search(r'data-edit-mode="([^"]*)"', html)
        batch_id_match = re.search(r'data-batch-id="([^"]*)"', html)
        block_id_match = re.search(r'data-block-id="([^"]*)"', html)
        
        edit_mode = edit_mode_match.group(1) if edit_mode_match else None
        batch_id_attr = batch_id_match.group(1) if batch_id_match else None
        block_id_attr = block_id_match.group(1) if block_id_match else None
        
        print(f"📊 Form data attributes:")
        print(f"  data-edit-mode: '{edit_mode}'")
        print(f"  data-batch-id: '{batch_id_attr}'")
        print(f"  data-block-id: '{block_id_attr}'")
        
        # Extract JavaScript batch_id
        js_batch_id_match = re.search(r"batch_id:\s*'([^']*)'", html)
        js_batch_id = js_batch_id_match.group(1) if js_batch_id_match else None
        
        print(f"📝 JavaScript batch_id: '{js_batch_id}'")
        
        # Validate expected values
        if edit_mode == 'true' and batch_id_attr and batch_id_attr != '' and js_batch_id and js_batch_id != '':
            print("✅ Form data attributes and JavaScript look correct")
            return True
        else:
            print("❌ Form data attributes or JavaScript are incorrect")
            print(f"   Expected: edit_mode='true', batch_id='{batch_id}', js_batch_id='{batch_id}'")
            print(f"   Actual: edit_mode='{edit_mode}', batch_id='{batch_id_attr}', js_batch_id='{js_batch_id}'")
            return False
            
    except Exception as e:
        print(f"❌ Error testing page: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing form initialization and data attributes...")
    success = test_edit_page_data_attributes()
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Tests failed!")