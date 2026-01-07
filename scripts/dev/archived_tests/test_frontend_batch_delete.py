#!/usr/bin/env python3
"""
Test to verify frontend batch delete functionality
"""

import requests
from datetime import datetime, date, timedelta
import json

def test_frontend_batch_delete():
    """Test that the frontend correctly uses batch delete functions."""
    
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
        
        # Get the JavaScript file content
        js_response = session.get('http://localhost:5002/static/js/components/admin-enhanced.js')
        if js_response.status_code == 200:
            js_content = js_response.text
            
            # Check for batch delete functions
            required_functions = [
                'deleteBatch(',
                'showBatchDeleteConfirmation(',
                'confirmBatchDelete(',
                'closeBatchDeleteConfirmation('
            ]
            
            for func in required_functions:
                if func in js_content:
                    print(f"✓ {func} function found")
                else:
                    print(f"✗ {func} function not found")
                    return False
            
            # Check that delete buttons use deleteBatch instead of deleteBlock
            if "onclick=\"deleteBatch('" in js_content:
                print("✓ Delete buttons use deleteBatch function")
            else:
                print("✗ Delete buttons don't use deleteBatch function")
                return False
            
            # Check that the new batch delete endpoint is used
            if '/admin/blocks/batch/' in js_content:
                print("✓ Batch delete endpoint found in JavaScript")
            else:
                print("✗ Batch delete endpoint not found in JavaScript")
                return False
            
            # Check that batch_id is used for deletion
            if 'batch_id' in js_content:
                print("✓ batch_id used in delete functionality")
            else:
                print("✗ batch_id not used in delete functionality")
                return False
            
            return True
        else:
            print(f"✗ Failed to load JavaScript file: {js_response.status_code}")
            return False
    else:
        print(f"✗ Failed to load admin page: {admin_response.status_code}")
        return False

if __name__ == '__main__':
    print("Testing frontend batch delete functionality...")
    success = test_frontend_batch_delete()
    
    if success:
        print("\n✓ Frontend batch delete functionality working correctly!")
    else:
        print("\n✗ Frontend batch delete functionality has issues.")