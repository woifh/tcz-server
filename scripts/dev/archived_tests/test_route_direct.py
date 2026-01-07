#!/usr/bin/env python3
"""
Test the route directly to see what's being returned
"""

import requests

def test_route():
    batch_id = "1d40fb5c-500c-4127-9c4a-05d9f53fe47f"
    url = f"http://127.0.0.1:5001/admin/court-blocking/{batch_id}"
    
    print(f"🔍 Testing URL: {url}")
    
    try:
        response = requests.get(url)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # Look for the data attributes in the response
            html = response.text
            
            # Find the form section
            form_start = html.find('<form id="multi-court-form"')
            if form_start == -1:
                print("❌ Form not found in response")
                return
                
            form_end = html.find('>', form_start) + 1
            form_tag = html[form_start:form_end]
            
            print(f"📝 Form tag: {form_tag}")
            
            # Look for JavaScript section
            js_start = html.find('window.editBlockData')
            if js_start != -1:
                js_end = html.find('};', js_start) + 2
                js_section = html[js_start:js_end]
                print(f"📝 JavaScript section: {js_section}")
            else:
                print("❌ JavaScript editBlockData not found")
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_route()