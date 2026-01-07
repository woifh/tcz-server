#!/usr/bin/env python3
"""Test HTTP request to the edit URL."""

import requests
import re

# Test the edit URL directly
url = "http://127.0.0.1:5000/admin/court-blocking/c685f92a-d747-4082-ab98-476d87c41876"

try:
    response = requests.get(url, allow_redirects=False)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        html_content = response.text
        
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
                print(f"data-edit-mode: '{edit_mode_match.group(1)}'")
            
            if batch_id_match:
                print(f"data-batch-id: '{batch_id_match.group(1)}'")
            else:
                print("❌ data-batch-id not found in form tag")
            
            if block_id_match:
                print(f"data-block-id: '{block_id_match.group(1)}'")
                
        else:
            print("❌ Form tag not found")
            
    elif response.status_code == 302:
        print(f"Redirect to: {response.headers.get('Location')}")
    else:
        print(f"Error response: {response.text[:500]}")
        
except requests.exceptions.ConnectionError:
    print("❌ Could not connect to server. Is it running?")
except Exception as e:
    print(f"❌ Error: {e}")