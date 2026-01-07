#!/usr/bin/env python3
"""
Test the edit route with proper authentication
"""

import requests
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Member

def test_authenticated_edit():
    app = create_app()
    
    with app.app_context():
        # Get an admin user
        admin = Member.query.filter_by(role='admin').first()
        if not admin:
            print("❌ No admin user found")
            return False
            
        print(f"✅ Found admin user: {admin.email}")
    
    # Create a test client
    with app.test_client() as client:
        # Login as admin
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin.id)
            sess['_fresh'] = True
        
        batch_id = "1d40fb5c-500c-4127-9c4a-05d9f53fe47f"
        url = f"/admin/court-blocking/{batch_id}"
        
        print(f"🔍 Testing authenticated request to: {url}")
        
        response = client.get(url)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            html = response.get_data(as_text=True)
            
            # Check for form data attributes
            if 'data-edit-mode="true"' in html:
                print("✅ Found data-edit-mode='true'")
            else:
                print("❌ data-edit-mode not set to true")
                
            if f'data-batch-id="{batch_id}"' in html:
                print(f"✅ Found correct batch_id in data attributes")
            else:
                print("❌ batch_id not found in data attributes")
                
            # Check JavaScript section
            if f"batch_id: '{batch_id}'" in html:
                print("✅ Found correct batch_id in JavaScript")
            else:
                print("❌ batch_id not found in JavaScript")
                
            # Look for debug output in console
            if "DEBUG:" in html:
                print("📝 Found debug output in response")
            
            return True
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.get_data(as_text=True)[:500]}")
            return False

if __name__ == "__main__":
    success = test_authenticated_edit()
    sys.exit(0 if success else 1)