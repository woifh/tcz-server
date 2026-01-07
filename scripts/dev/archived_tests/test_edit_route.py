#!/usr/bin/env python3
"""Test the edit route directly."""

import sys
sys.path.append('.')
from app import create_app, db
from app.models import Block, Member
from flask import url_for

app = create_app()

with app.test_client() as client:
    with app.app_context():
        # Get the first block with batch_id
        block = Block.query.filter(Block.batch_id.isnot(None)).first()
        
        if not block:
            print("No blocks with batch_id found")
            sys.exit(1)
        
        print(f"Testing edit route for batch_id: {block.batch_id}")
        
        # Login as admin first
        admin = Member.query.filter_by(role='admin').first()
        if not admin:
            print("No admin user found")
            sys.exit(1)
        
        # Simulate login (this is a simplified approach)
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin.id)
            sess['_fresh'] = True
        
        # Test the edit route
        response = client.get(f'/admin/court-blocking/{block.batch_id}')
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            # Look for the data-batch-id attribute in the response
            html_content = response.get_data(as_text=True)
            
            # Find the form with data-batch-id
            import re
            batch_id_match = re.search(r'data-batch-id="([^"]*)"', html_content)
            
            if batch_id_match:
                found_batch_id = batch_id_match.group(1)
                print(f"Found data-batch-id in HTML: '{found_batch_id}'")
                
                if found_batch_id == block.batch_id:
                    print("✅ Batch ID is correctly set in the template!")
                else:
                    print(f"❌ Batch ID mismatch. Expected: {block.batch_id}, Found: {found_batch_id}")
            else:
                print("❌ data-batch-id attribute not found in HTML")
                
                # Look for the form element
                form_match = re.search(r'<form[^>]*id="multi-court-form"[^>]*>', html_content)
                if form_match:
                    print(f"Form element found: {form_match.group(0)}")
                else:
                    print("Form element not found")
        else:
            print(f"Request failed with status {response.status_code}")
            print(f"Response: {response.get_data(as_text=True)[:500]}")