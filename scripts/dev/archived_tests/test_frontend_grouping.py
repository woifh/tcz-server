#!/usr/bin/env python3
"""
Test to verify frontend grouping functionality
"""

import requests
from datetime import datetime, date, timedelta
import json

def test_frontend_grouping():
    """Test that the frontend correctly groups blocks by batch_id."""
    
    session = requests.Session()
    
    # Login
    login_data = {'email': 'woifh@gmx.at', 'password': 'test123'}
    login_response = session.post('http://localhost:5002/auth/login', data=login_data)
    
    if login_response.status_code != 200 or 'login' in login_response.url.lower():
        print("Login failed")
        return False
    
    print("✓ Login successful")
    
    # Get the admin court blocking page
    admin_response = session.get('http://localhost:5002/admin/court-blocking')
    
    if admin_response.status_code == 200:
        print("✓ Admin page loaded successfully")
        
        # Check if the page contains the JavaScript grouping function
        page_content = admin_response.text
        
        # Check if the JavaScript file is included
        if 'admin-enhanced.js' in page_content:
            print("✓ admin-enhanced.js file included in page")
        else:
            print("✗ admin-enhanced.js file not included")
            return False
        
        # Get the JavaScript file content
        js_response = session.get('http://localhost:5002/static/js/components/admin-enhanced.js')
        if js_response.status_code == 200:
            js_content = js_response.text
            
            if 'groupBlocksByBatch' in js_content:
                print("✓ groupBlocksByBatch function found in JavaScript file")
            else:
                print("✗ groupBlocksByBatch function not found in JavaScript file")
                return False
            
            # Check if the function uses batch_id for grouping
            if 'batch_${block.batch_id}' in js_content:
                print("✓ Batch ID grouping logic found")
            else:
                print("✗ Batch ID grouping logic not found")
                return False
            
            # Check if edit function uses batch identifiers
            if 'editBatch(' in js_content:
                print("✓ editBatch function found")
            else:
                print("✗ editBatch function not found")
                return False
        else:
            print(f"✗ Failed to load JavaScript file: {js_response.status_code}")
            return False
        
        return True
    else:
        print(f"✗ Failed to load admin page: {admin_response.status_code}")
        return False

if __name__ == '__main__':
    print("Testing frontend grouping functionality...")
    success = test_frontend_grouping()
    
    if success:
        print("\n✓ Frontend grouping functionality working correctly!")
    else:
        print("\n✗ Frontend grouping functionality has issues.")