#!/usr/bin/env python3
"""
Test the specific batch_id fix for the user's case
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Block
from flask import render_template_string

def test_specific_batch_fix():
    """Test the fix for the specific batch_id"""
    app = create_app()
    
    with app.app_context():
        # Test with the user's specific batch_id
        test_batch_id = '1d40fb5c-500c-4127-9c4a-05d9f53fe47f'
        
        # Create test edit_block_data as the route would
        edit_block_data = {
            'id': 1,
            'batch_id': test_batch_id,
            'court_ids': [1, 2],
            'date': '2026-01-03',
            'start_time': '10:00',
            'end_time': '12:00',
            'reason_id': 1,
            'details': 'Test blocking',
            'description': '',
            'related_block_ids': [1, 2]
        }
        
        print(f"✅ Testing with batch_id: {test_batch_id}")
        
        # Test the HTML data attribute template
        html_template = """
        data-batch-id="{{ edit_block_data.batch_id if (edit_block_data.batch_id and edit_block_data.batch_id != 'None' and edit_block_data.batch_id != 'null') else '' }}"
        """
        
        html_result = render_template_string(html_template, edit_block_data=edit_block_data)
        print(f"🎯 HTML data attribute: {html_result.strip()}")
        
        # Test the JavaScript template
        js_template = """
        batch_id: '{{ edit_block_data.batch_id if (edit_block_data.batch_id and edit_block_data.batch_id != 'None' and edit_block_data.batch_id != 'null') else '' }}',
        """
        
        js_result = render_template_string(js_template, edit_block_data=edit_block_data)
        print(f"🎯 JavaScript batch_id: {js_result.strip()}")
        
        # Test with None value (what was causing the issue)
        edit_block_data_none = edit_block_data.copy()
        edit_block_data_none['batch_id'] = None
        
        html_result_none = render_template_string(html_template, edit_block_data=edit_block_data_none)
        js_result_none = render_template_string(js_template, edit_block_data=edit_block_data_none)
        
        print(f"\n❌ With None batch_id:")
        print(f"   HTML data attribute: {html_result_none.strip()}")
        print(f"   JavaScript batch_id: {js_result_none.strip()}")
        
        # Test with 'None' string value
        edit_block_data_str_none = edit_block_data.copy()
        edit_block_data_str_none['batch_id'] = 'None'
        
        html_result_str_none = render_template_string(html_template, edit_block_data=edit_block_data_str_none)
        js_result_str_none = render_template_string(js_template, edit_block_data=edit_block_data_str_none)
        
        print(f"\n❌ With 'None' string batch_id:")
        print(f"   HTML data attribute: {html_result_str_none.strip()}")
        print(f"   JavaScript batch_id: {js_result_str_none.strip()}")
        
        # Verify the fix works
        if test_batch_id in html_result and test_batch_id in js_result:
            print(f"\n✅ Fix works correctly - batch_id is properly set in both HTML and JavaScript")
        else:
            print(f"\n❌ Fix failed - batch_id not found in templates")
        
        if html_result_none.strip() == 'data-batch-id=""' and 'batch_id: \'\'' in js_result_none:
            print(f"✅ None values are handled correctly - empty strings generated")
        else:
            print(f"❌ None values not handled correctly")

if __name__ == '__main__':
    test_specific_batch_fix()