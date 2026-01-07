#!/usr/bin/env python3
"""
Minimal test to verify the edit functionality
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Block

def test_minimal_edit():
    """Test the minimal edit functionality"""
    app = create_app()
    
    with app.app_context():
        # Get a block with a valid batch_id
        block = Block.query.filter(Block.batch_id.isnot(None)).first()
        
        if not block:
            print("❌ No blocks with batch_id found")
            return
        
        print(f"✅ Found block with batch_id: {block.batch_id}")
        print(f"   Block ID: {block.id}")
        print(f"   Court ID: {block.court_id}")
        print(f"   Date: {block.date}")
        print(f"   Time: {block.start_time} - {block.end_time}")
        
        # Test the edit URL
        edit_url = f"/admin/court-blocking/{block.batch_id}"
        print(f"\n🔗 Edit URL: {edit_url}")
        
        # Test what the route should create
        actual_batch_id = block.batch_id.replace('batch_', '') if block.batch_id.startswith('batch_') else block.batch_id
        
        # Get all blocks with this batch_id
        blocks = Block.query.filter_by(batch_id=actual_batch_id).all()
        print(f"\n📊 Blocks in batch:")
        for b in blocks:
            print(f"   Block {b.id}: Court {b.court_id}, {b.date} {b.start_time}-{b.end_time}")
        
        # Create the edit_block_data that the route should create
        primary_block = blocks[0]
        court_ids = [b.court_id for b in blocks]
        
        edit_block_data = {
            'id': primary_block.id,
            'batch_id': actual_batch_id,
            'court_ids': court_ids,
            'date': primary_block.date,
            'start_time': primary_block.start_time,
            'end_time': primary_block.end_time,
            'reason_id': primary_block.reason_id,
            'details': primary_block.details,
            'created_by': primary_block.created_by_id,
            'created_at': primary_block.created_at,
            'related_block_ids': [b.id for b in blocks]
        }
        
        print(f"\n📋 edit_block_data that should be passed to template:")
        for key, value in edit_block_data.items():
            print(f"   {key}: {value}")
        
        # Test the template condition
        batch_id = edit_block_data.get('batch_id')
        condition_result = batch_id if (edit_block_data and batch_id and batch_id != 'None' and batch_id != 'null') else ''
        
        print(f"\n🎯 Template condition result:")
        print(f"   data-batch-id=\"{condition_result}\"")
        
        if condition_result:
            print(f"   ✅ Should work - batch_id will be set to: '{condition_result}'")
        else:
            print(f"   ❌ Will not work - batch_id will be empty")

if __name__ == '__main__':
    test_minimal_edit()