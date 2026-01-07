#!/usr/bin/env python3
"""
Test what the template is actually rendering
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Block

def test_template_rendering():
    app = create_app()
    
    with app.test_client() as client:
        with app.app_context():
            batch_id = "1d40fb5c-500c-4127-9c4a-05d9f53fe47f"
            
            # Get the blocks to see what data we have
            blocks = Block.query.filter_by(batch_id=batch_id).all()
            print(f"📊 Found {len(blocks)} blocks with batch_id {batch_id}")
            
            if not blocks:
                print("❌ No blocks found")
                return False
            
            # Simulate what the route does
            primary_block = blocks[0]
            court_ids = [block.court_id for block in blocks]
            
            edit_block_data = {
                'id': primary_block.id,
                'batch_id': batch_id,
                'court_ids': court_ids,
                'date': primary_block.date,
                'start_time': primary_block.start_time,
                'end_time': primary_block.end_time,
                'reason_id': primary_block.reason_id,
                'details': primary_block.details,
                'created_by_id': primary_block.created_by_id,
                'created_at': primary_block.created_at,
                'related_block_ids': [block.id for block in blocks]
            }
            
            print(f"📝 edit_block_data that would be passed to template:")
            print(f"  id: {edit_block_data['id']}")
            print(f"  batch_id: '{edit_block_data['batch_id']}'")
            print(f"  batch_id type: {type(edit_block_data['batch_id'])}")
            print(f"  court_ids: {edit_block_data['court_ids']}")
            
            # Test the template conditions
            has_edit_data = bool(edit_block_data)
            has_batch_id = bool(edit_block_data.get('batch_id'))
            batch_id_not_none = edit_block_data.get('batch_id') != 'None'
            batch_id_not_null = edit_block_data.get('batch_id') != 'null'
            
            print(f"\n🔍 Template condition checks:")
            print(f"  edit_block_data exists: {has_edit_data}")
            print(f"  batch_id exists: {has_batch_id}")
            print(f"  batch_id != 'None': {batch_id_not_none}")
            print(f"  batch_id != 'null': {batch_id_not_null}")
            
            # Simulate the template rendering logic
            data_edit_mode = 'true' if edit_block_data else 'false'
            data_block_id = edit_block_data['id'] if edit_block_data else ''
            
            # This is the critical line from the template
            condition = (edit_block_data and 
                        edit_block_data.get('batch_id') and 
                        edit_block_data.get('batch_id') != 'None' and 
                        edit_block_data.get('batch_id') != 'null')
            
            data_batch_id = edit_block_data['batch_id'] if condition else ''
            
            print(f"\n📋 What would be rendered in HTML:")
            print(f"  data-edit-mode=\"{data_edit_mode}\"")
            print(f"  data-block-id=\"{data_block_id}\"")
            print(f"  data-batch-id=\"{data_batch_id}\"")
            
            if data_batch_id == '':
                print(f"\n❌ PROBLEM: data-batch-id would be empty!")
                print(f"   This means the template condition failed")
                print(f"   Condition result: {condition}")
            else:
                print(f"\n✅ data-batch-id would be correctly set")
            
            return data_batch_id != ''

if __name__ == "__main__":
    success = test_template_rendering()
    print(f"\n{'✅ Template rendering looks correct' if success else '❌ Template rendering has issues'}")
    sys.exit(0 if success else 1)