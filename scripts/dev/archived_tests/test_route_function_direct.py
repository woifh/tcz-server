#!/usr/bin/env python3
"""
Test the route function directly without authentication
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Block, Member
from flask import Flask
import re

def test_route_function_direct():
    """Test the route function directly"""
    app = create_app()
    
    with app.app_context():
        # Get a block with a valid batch_id
        block = Block.query.filter(Block.batch_id.isnot(None)).first()
        
        if not block:
            print("❌ No blocks with batch_id found")
            return
        
        print(f"✅ Found block with batch_id: {block.batch_id}")
        
        # Import the route function directly
        from app.routes.admin import court_blocking_edit_batch
        
        # Create a test request context
        with app.test_request_context(f'/admin/court-blocking/{block.batch_id}'):
            # Mock the current_user for admin access
            from flask_login import login_user
            admin_user = Member.query.filter_by(role='admin').first()
            
            if not admin_user:
                print("❌ No admin user found")
                return
            
            # Login the admin user
            login_user(admin_user)
            
            try:
                # Call the route function directly
                result = court_blocking_edit_batch(block.batch_id)
                
                # Check if it's a response object
                if hasattr(result, 'get_data'):
                    html_content = result.get_data(as_text=True)
                    
                    # Save the HTML to a file for inspection
                    with open('debug_route_direct_html.html', 'w') as f:
                        f.write(html_content)
                    print("HTML saved to debug_route_direct_html.html")
                    
                    # Look for the data-batch-id attribute in the HTML
                    batch_id_match = re.search(r'data-batch-id="([^"]*)"', html_content)
                    
                    if batch_id_match:
                        found_batch_id = batch_id_match.group(1)
                        print(f"✅ Found data-batch-id in HTML: '{found_batch_id}'")
                        
                        if found_batch_id == block.batch_id:
                            print(f"✅ Batch ID matches expected value")
                        else:
                            print(f"❌ Batch ID mismatch. Expected: '{block.batch_id}', Found: '{found_batch_id}'")
                    else:
                        print(f"❌ data-batch-id attribute not found in HTML")
                        
                        # Look for the form element
                        form_match = re.search(r'<form[^>]*id="multi-court-form"[^>]*>', html_content)
                        if form_match:
                            print(f"Form element found: {form_match.group(0)}")
                        else:
                            print(f"❌ Form element not found")
                    
                    # Check if edit_block_data is mentioned in the HTML
                    if 'edit_block_data' in html_content:
                        print("✅ edit_block_data found in HTML")
                    else:
                        print("❌ edit_block_data not found in HTML")
                        
                    # Check for the JavaScript section
                    if 'window.editBlockData' in html_content:
                        print("✅ window.editBlockData found in HTML")
                        
                        # Extract the JavaScript data
                        js_match = re.search(r'window\.editBlockData = ({[^}]+});', html_content)
                        if js_match:
                            print(f"JavaScript data: {js_match.group(1)}")
                    else:
                        print("❌ window.editBlockData not found in HTML")
                        
                else:
                    print(f"Route returned: {result}")
                    
            except Exception as e:
                print(f"❌ Error calling route function: {e}")
                import traceback
                traceback.print_exc()

if __name__ == '__main__':
    test_route_function_direct()