#!/usr/bin/env python3

import subprocess
import json
import sys

def run_curl(url, method='GET', data=None, headers=None):
    """Run curl command and return response."""
    cmd = ['curl', '-s']
    
    if method != 'GET':
        cmd.extend(['-X', method])
    
    if headers:
        for key, value in headers.items():
            cmd.extend(['-H', f'{key}: {value}'])
    
    if data:
        cmd.extend(['-d', json.dumps(data)])
    
    cmd.append(url)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, '', 'Timeout'

def test_batch_id():
    """Test the current batch_id behavior."""
    
    print("🔧 Testing current batch_id behavior...")
    
    # First, let's check if we can access the admin page
    code, stdout, stderr = run_curl('http://127.0.0.1:5001/admin/court-blocking')
    
    if code != 0:
        print(f"❌ Failed to access admin page: {stderr}")
        return False
    
    if 'Platz-Sperrungen' not in stdout:
        print("❌ Admin page doesn't contain expected content")
        return False
    
    print("✅ Admin page accessible")
    
    # Let's check if there are any existing blocks we can use for testing
    code, stdout, stderr = run_curl('http://127.0.0.1:5001/admin/blocks')
    
    if code == 0:
        try:
            blocks_data = json.loads(stdout)
            blocks = blocks_data.get('blocks', [])
            
            if blocks:
                # Use the first block's batch_id for testing
                batch_id = blocks[0].get('batch_id')
                if batch_id:
                    print(f"📋 Found existing batch_id: {batch_id}")
                    
                    # Test the edit page
                    edit_url = f'http://127.0.0.1:5001/admin/court-blocking/{batch_id}'
                    code, html_content, stderr = run_curl(edit_url)
                    
                    if code == 0:
                        print("✅ Edit page accessible")
                        
                        # Check for data-batch-id attribute
                        if f'data-batch-id="{batch_id}"' in html_content:
                            print(f"✅ data-batch-id correctly set to: {batch_id}")
                        else:
                            print("❌ data-batch-id not correctly set")
                            # Look for the actual value
                            import re
                            match = re.search(r'data-batch-id="([^"]*)"', html_content)
                            if match:
                                actual_value = match.group(1)
                                print(f"   Actual value: '{actual_value}'")
                            else:
                                print("   No data-batch-id attribute found")
                        
                        # Check for window.editBlockData.batch_id
                        if f"batch_id: '{batch_id}'" in html_content:
                            print(f"✅ window.editBlockData.batch_id correctly set to: {batch_id}")
                        else:
                            print("❌ window.editBlockData.batch_id not correctly set")
                            # Look for the actual value
                            import re
                            match = re.search(r"batch_id: '([^']*)'", html_content)
                            if match:
                                actual_value = match.group(1)
                                print(f"   Actual value: '{actual_value}'")
                            else:
                                print("   No batch_id found in JavaScript")
                        
                        return True
                    else:
                        print(f"❌ Failed to access edit page: {stderr}")
                        return False
                else:
                    print("❌ No batch_id found in existing blocks")
            else:
                print("ℹ️ No existing blocks found")
        except json.JSONDecodeError:
            print(f"❌ Failed to parse blocks response: {stdout[:200]}...")
    
    print("ℹ️ Will create a test batch for testing...")
    return True

if __name__ == '__main__':
    success = test_batch_id()
    sys.exit(0 if success else 1)