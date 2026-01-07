#!/usr/bin/env python3
"""Test authenticated request to the edit URL."""

import sys
sys.path.append('.')
from app import create_app, db
from app.models import Block, Member
import re

app = create_app()

with app.test_client() as client:
    with app.app_context():
        # Get the first block with batch_id
        block = Block.query.filter(Block.batch_id.isnot(None)).first()
        
        if not block:
            print("No blocks with batch_id found")
            sys.exit(1)
        
        # Get admin user
        admin = Member.query.filter_by(role='admin').first()
        if not admin:
            print("No admin user found")
            sys.exit(1)
        
        print(f"Testing authenticated request for batch_id: {block.batch_id}")
        
        # Login first
        login_response = client.post('/auth/login', data={
            'email': admin.email,
            'password': 'test'  # This won't work with hashed passwords, but let's try
        })
        
        print(f"Login response status: {login_response.status_code}")
        
        # Try a different approach - simulate session
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin.id)
            sess['_fresh'] = True
        
        # Now test the edit URL
        response = client.get(f'/admin/court-blocking/{block.batch_id}')
        
        print(f"Edit page status: {response.status_code}")
        
        if response.status_code == 200:
            html_content = response.get_data(as_text=True)
            
            # Look for the form tag
            form_match = re.search(r'<form[^>]*id="multi-court-form"[^>]*>', html_content)
            
            if form_match:
                form_tag = form_match.group(0)
                print(f"Form tag found: {form_tag}")
                
                # Extract data attributes
                edit_mode_match = re.search(r'data-edit-mode="([^"]*)"', form_tag)
                batch_id_match = re.search(r'data-batch-id="([^"]*)"', form_tag)
                block_id_match = re.search(r'data-block-id="([^"]*)"', form_tag)
                
                if edit_mode_match:
                    print(f"✅ data-edit-mode: '{edit_mode_match.group(1)}'")
                
                if batch_id_match:
                    batch_id_value = batch_id_match.group(1)
                    print(f"✅ data-batch-id: '{batch_id_value}'")
                    
                    if batch_id_value == block.batch_id:
                        print("🎉 SUCCESS: Batch ID is correctly set in the template!")
                    elif batch_id_value == '':
                        print("❌ ISSUE: Batch ID is empty string")
                    else:
                        print(f"❌ ISSUE: Batch ID mismatch. Expected: {block.batch_id}, Found: {batch_id_value}")
                else:
                    print("❌ ISSUE: data-batch-id not found in form tag")
                
                if block_id_match:
                    print(f"✅ data-block-id: '{block_id_match.group(1)}'")
                    
            else:
                print("❌ Form tag not found")
                # Print first 1000 chars to debug
                print(f"HTML content (first 1000 chars): {html_content[:1000]}")
                
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.get_data(as_text=True)[:500]}")