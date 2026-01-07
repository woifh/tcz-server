#!/usr/bin/env python3
"""
Debug script to test the actual route and template rendering
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Block
from flask import url_for

def test_actual_route():
    """Test the actual route that renders the template"""
    app = create_app()
    
    with app.app_context():
        # Get a block with a valid batch_id
        block = Block.query.filter(Block.batch_id.isnot(None)).first()
        
        if not block:
            print("❌ No blocks with batch_id found")
            return
        
        print(f"✅ Found block with batch_id: {block.batch_id}")
        print(f"   Block ID: {block.id}")
        
        # Test the actual route
        with app.test_client() as client:
            # Login as admin first
            from app.models import Member
            admin_user = Member.query.filter_by(role='admin').first()
            if not admin_user:
                print("❌ No admin user found")
                return
            
            # Simulate login
            with client.session_transaction() as sess:
                sess['_user_id'] = str(admin_user.id)
                sess['_fresh'] = True
            
            # Test the batch edit route
            batch_id = block.batch_id
            response = client.get(f'/admin/court-blocking/{batch_id}')
            
            print(f"\n📊 Route response:")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                html_content = response.get_data(as_text=True)
                
                # Look for the data-batch-id attribute in the HTML
                import re
                batch_id_match = re.search(r'data-batch-id="([^"]*)"', html_content)
                
                if batch_id_match:
                    found_batch_id = batch_id_match.group(1)
                    print(f"   ✅ Found data-batch-id in HTML: '{found_batch_id}'")
                    
                    if found_batch_id == batch_id:
                        print(f"   ✅ Batch ID matches expected value")
                    else:
                        print(f"   ❌ Batch ID mismatch. Expected: '{batch_id}', Found: '{found_batch_id}'")
                else:
                    print(f"   ❌ data-batch-id attribute not found in HTML")
                    
                    # Look for the form element
                    form_match = re.search(r'<form[^>]*id="multi-court-form"[^>]*>', html_content)
                    if form_match:
                        print(f"   Form element found: {form_match.group(0)}")
                    else:
                        print(f"   ❌ Form element not found")
                
                # Also check for edit mode
                edit_mode_match = re.search(r'data-edit-mode="([^"]*)"', html_content)
                if edit_mode_match:
                    print(f"   Edit mode: {edit_mode_match.group(1)}")
                
            else:
                print(f"   ❌ Route failed with status {response.status_code}")
                print(f"   Response: {response.get_data(as_text=True)}")

if __name__ == '__main__':
    test_actual_route()