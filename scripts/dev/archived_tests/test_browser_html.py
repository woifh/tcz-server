#!/usr/bin/env python3
"""
Test script to fetch HTML from the running server
"""

import requests
import re
import sys

def test_browser_html():
    """Test the actual HTML from the browser"""
    
    # First, login to get a session
    session = requests.Session()
    
    # Try to login
    login_data = {
        'email': 'admin@tennisclub.de',
        'password': 'admin123'
    }
    
    try:
        # Login
        login_response = session.post('http://127.0.0.1:5001/auth/login', data=login_data)
        print(f"Login response: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print("❌ Login failed")
            return
        
        # Now try to access the edit page
        batch_id = 'c685f92a-d747-4082-ab98-476d87c41876'
        edit_url = f'http://127.0.0.1:5001/admin/court-blocking/{batch_id}'
        
        response = session.get(edit_url)
        print(f"Edit page response: {response.status_code}")
        
        if response.status_code == 200:
            html_content = response.text
            
            # Save the HTML to a file for inspection
            with open('debug_actual_html.html', 'w') as f:
                f.write(html_content)
            print("HTML saved to debug_actual_html.html")
            
            # Look for the data-batch-id attribute in the HTML
            batch_id_match = re.search(r'data-batch-id="([^"]*)"', html_content)
            
            if batch_id_match:
                found_batch_id = batch_id_match.group(1)
                print(f"✅ Found data-batch-id in HTML: '{found_batch_id}'")
                
                if found_batch_id == batch_id:
                    print(f"✅ Batch ID matches expected value")
                else:
                    print(f"❌ Batch ID mismatch. Expected: '{batch_id}', Found: '{found_batch_id}'")
            else:
                print(f"❌ data-batch-id attribute not found in HTML")
                
                # Look for the form element
                form_match = re.search(r'<form[^>]*id="multi-court-form"[^>]*>', html_content)
                if form_match:
                    print(f"Form element found: {form_match.group(0)}")
                else:
                    print(f"❌ Form element not found")
                    
                    # Look for any form elements
                    all_forms = re.findall(r'<form[^>]*>', html_content)
                    print(f"All forms found: {len(all_forms)}")
                    for i, form in enumerate(all_forms):
                        print(f"  Form {i+1}: {form}")
            
            # Also check for edit mode
            edit_mode_match = re.search(r'data-edit-mode="([^"]*)"', html_content)
            if edit_mode_match:
                print(f"Edit mode: {edit_mode_match.group(1)}")
            
            # Check for JavaScript console logs in the HTML
            console_log_match = re.search(r'console\.log\([^)]*editBlockData[^)]*\)', html_content)
            if console_log_match:
                print(f"Found console.log for editBlockData: {console_log_match.group(0)}")
                
            # Check if edit_block_data is mentioned in the HTML
            if 'edit_block_data' in html_content:
                print("✅ edit_block_data found in HTML")
            else:
                print("❌ edit_block_data not found in HTML")
                
        else:
            print(f"❌ Failed to access edit page: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_browser_html()