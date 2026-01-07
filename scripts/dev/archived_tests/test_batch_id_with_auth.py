#!/usr/bin/env python3

import subprocess
import json
import sys
import tempfile
import os

def run_curl_with_cookies(url, method='GET', data=None, headers=None, cookie_jar=None):
    """Run curl command with cookie support."""
    cmd = ['curl', '-s']
    
    if cookie_jar:
        cmd.extend(['-c', cookie_jar, '-b', cookie_jar])
    
    if method != 'GET':
        cmd.extend(['-X', method])
    
    if headers:
        for key, value in headers.items():
            cmd.extend(['-H', f'{key}: {value}'])
    
    if data:
        if isinstance(data, dict):
            # Form data
            for key, value in data.items():
                cmd.extend(['-d', f'{key}={value}'])
        else:
            # JSON data
            cmd.extend(['-H', 'Content-Type: application/json', '-d', data])
    
    cmd.append(url)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, '', 'Timeout'

def test_with_auth():
    """Test batch_id with proper authentication."""
    
    print("🔧 Testing batch_id with authentication...")
    
    # Create a temporary cookie jar
    with tempfile.NamedTemporaryFile(delete=False) as cookie_file:
        cookie_jar = cookie_file.name
    
    try:
        # Step 1: Login
        print("🔑 Logging in...")
        login_data = {
            'email': 'admin@tennisclub.de',
            'password': 'admin123'
        }
        
        code, stdout, stderr = run_curl_with_cookies(
            'http://127.0.0.1:5001/auth/login',
            method='POST',
            data=login_data,
            cookie_jar=cookie_jar
        )
        
        if code != 0:
            print(f"❌ Login request failed: {stderr}")
            return False
        
        print("✅ Login request completed")
        
        # Step 2: Create a test batch
        print("📝 Creating test batch...")
        block_data = {
            'court_ids': [1, 2],
            'date': '2026-01-04',
            'start_time': '14:00',
            'end_time': '16:00',
            'reason_id': 1,
            'details': 'Test batch ID check'
        }
        
        code, stdout, stderr = run_curl_with_cookies(
            'http://127.0.0.1:5001/admin/blocks/multi-court',
            method='POST',
            data=json.dumps(block_data),
            headers={'Content-Type': 'application/json'},
            cookie_jar=cookie_jar
        )
        
        if code != 0:
            print(f"❌ Block creation failed: {stderr}")
            return False
        
        try:
            create_response = json.loads(stdout)
            print(f"✅ Test batch created: {create_response.get('message', 'Success')}")
        except json.JSONDecodeError:
            print(f"⚠️ Block creation response: {stdout[:100]}...")
        
        # Step 3: Get blocks to find our batch_id
        print("🔍 Finding batch_id...")
        code, stdout, stderr = run_curl_with_cookies(
            'http://127.0.0.1:5001/admin/blocks?date=2026-01-04',
            cookie_jar=cookie_jar
        )
        
        if code != 0:
            print(f"❌ Failed to get blocks: {stderr}")
            return False
        
        try:
            blocks_data = json.loads(stdout)
            test_blocks = [b for b in blocks_data['blocks'] if b.get('details') == 'Test batch ID check']
            
            if not test_blocks:
                print("❌ Test blocks not found")
                return False
            
            batch_id = test_blocks[0]['batch_id']
            print(f"📋 Found batch_id: {batch_id}")
            
            # Step 4: Test the edit page
            print("🔍 Testing edit page...")
            edit_url = f'http://127.0.0.1:5001/admin/court-blocking/{batch_id}'
            code, html_content, stderr = run_curl_with_cookies(edit_url, cookie_jar=cookie_jar)
            
            if code != 0:
                print(f"❌ Failed to access edit page: {stderr}")
                return False
            
            print("✅ Edit page accessible")
            
            # Check data-batch-id attribute
            if f'data-batch-id="{batch_id}"' in html_content:
                print(f"✅ data-batch-id correctly set to: {batch_id}")
            else:
                print("❌ data-batch-id not correctly set")
                import re
                match = re.search(r'data-batch-id="([^"]*)"', html_content)
                if match:
                    actual_value = match.group(1)
                    print(f"   Actual value: '{actual_value}'")
                else:
                    print("   No data-batch-id attribute found")
            
            # Check window.editBlockData.batch_id
            if f"batch_id: '{batch_id}'" in html_content:
                print(f"✅ window.editBlockData.batch_id correctly set to: {batch_id}")
            else:
                print("❌ window.editBlockData.batch_id not correctly set")
                import re
                match = re.search(r"batch_id: '([^']*)'", html_content)
                if match:
                    actual_value = match.group(1)
                    print(f"   Actual value: '{actual_value}'")
                else:
                    print("   No batch_id found in JavaScript")
            
            # Step 5: Clean up
            print("🧹 Cleaning up...")
            code, stdout, stderr = run_curl_with_cookies(
                f'http://127.0.0.1:5001/admin/blocks/batch/{batch_id}',
                method='DELETE',
                cookie_jar=cookie_jar
            )
            
            if code == 0:
                print("✅ Test batch cleaned up")
            else:
                print(f"⚠️ Failed to clean up: {stderr}")
            
            return True
            
        except json.JSONDecodeError:
            print(f"❌ Failed to parse blocks response: {stdout[:200]}...")
            return False
    
    finally:
        # Clean up cookie file
        try:
            os.unlink(cookie_jar)
        except:
            pass

if __name__ == '__main__':
    success = test_with_auth()
    sys.exit(0 if success else 1)