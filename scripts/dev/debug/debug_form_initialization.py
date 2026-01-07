#!/usr/bin/env python3
"""
Debug script to test form initialization and data attribute handling
"""

import requests
import sys
from bs4 import BeautifulSoup

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
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the form element
        form = soup.find('form', {'id': 'multi-court-form'})
        if not form:
            print("❌ Form element not found")
            return False
            
        # Check data attributes
        edit_mode = form.get('data-edit-mode')
        batch_id_attr = form.get('data-batch-id')
        block_id_attr = form.get('data-block-id')
        
        print(f"📊 Form data attributes:")
        print(f"  data-edit-mode: '{edit_mode}'")
        print(f"  data-batch-id: '{batch_id_attr}'")
        print(f"  data-block-id: '{block_id_attr}'")
        
        # Check JavaScript section
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string and 'window.editBlockData' in script.string:
                print(f"📝 Found JavaScript section with editBlockData")
                # Extract the batch_id line
                lines = script.string.split('\n')
                for line in lines:
                    if 'batch_id:' in line:
                        print(f"  JavaScript batch_id line: {line.strip()}")
                        break
                break
        
        # Validate expected values
        if edit_mode == 'true' and batch_id_attr and batch_id_attr != '':
            print("✅ Form data attributes look correct")
            return True
        else:
            print("❌ Form data attributes are incorrect")
            return False
            
    except Exception as e:
        print(f"❌ Error testing page: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing form initialization and data attributes...")
    success = test_edit_page_data_attributes()
    sys.exit(0 if success else 1)