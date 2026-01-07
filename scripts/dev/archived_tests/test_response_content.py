#!/usr/bin/env python3
"""
Check what's actually being returned by the route
"""

import requests

def test_response():
    batch_id = "1d40fb5c-500c-4127-9c4a-05d9f53fe47f"
    url = f"http://127.0.0.1:5001/admin/court-blocking/{batch_id}"
    
    print(f"🔍 Testing URL: {url}")
    
    try:
        response = requests.get(url)
        print(f"📊 Status Code: {response.status_code}")
        print(f"📊 Headers: {dict(response.headers)}")
        
        # Check if it's a redirect
        if response.status_code in [301, 302, 303, 307, 308]:
            print(f"🔄 Redirect to: {response.headers.get('Location')}")
        
        # Print first 1000 characters of response
        content = response.text[:1000]
        print(f"📝 Response content (first 1000 chars):")
        print(content)
        print("...")
        
        # Check if it contains login form (authentication issue)
        if "login" in content.lower() or "anmelden" in content.lower():
            print("🔐 Response contains login form - authentication required")
        
        # Check if it contains error message
        if "fehler" in content.lower() or "error" in content.lower():
            print("❌ Response contains error message")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_response()