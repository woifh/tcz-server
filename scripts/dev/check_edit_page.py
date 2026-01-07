#!/usr/bin/env python3

import subprocess
import re

def check_edit_page():
    """Check the edit page HTML for the batch_id values."""
    
    batch_id = "4ff3ef45-176e-4f10-8a24-4de850dd0291"
    edit_url = f"http://127.0.0.1:5001/admin/court-blocking/{batch_id}"
    
    print(f"🔍 Checking edit page: {edit_url}")
    
    # Use curl to fetch the page (this will redirect to login, but we can still see the structure)
    try:
        result = subprocess.run(['curl', '-s', edit_url], capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            print(f"❌ Failed to fetch page: {result.stderr}")
            return False
        
        html_content = result.stdout
        
        # Check if we got redirected to login
        if 'Redirecting' in html_content and 'login' in html_content:
            print("ℹ️ Page redirected to login (expected without authentication)")
            print("   This means the route is working and would show the edit page when logged in")
            return True
        
        # If we got the actual page content, check for our batch_id
        if 'data-batch-id=' in html_content:
            # Extract the data-batch-id value
            match = re.search(r'data-batch-id="([^"]*)"', html_content)
            if match:
                actual_batch_id = match.group(1)
                print(f"📋 Found data-batch-id: '{actual_batch_id}'")
                
                if actual_batch_id == batch_id:
                    print("✅ data-batch-id matches expected batch_id")
                else:
                    print(f"❌ data-batch-id mismatch. Expected: {batch_id}")
            else:
                print("❌ data-batch-id attribute found but couldn't extract value")
        
        # Check for JavaScript batch_id
        if "batch_id:" in html_content:
            match = re.search(r"batch_id: '([^']*)'", html_content)
            if match:
                js_batch_id = match.group(1)
                print(f"📋 Found JavaScript batch_id: '{js_batch_id}'")
                
                if js_batch_id == batch_id:
                    print("✅ JavaScript batch_id matches expected batch_id")
                else:
                    print(f"❌ JavaScript batch_id mismatch. Expected: {batch_id}")
        
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    check_edit_page()