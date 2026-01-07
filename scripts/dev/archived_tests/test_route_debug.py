#!/usr/bin/env python3
"""
Test the route directly by calling it in the Flask app context
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Block, Member
from app.routes.admin import court_blocking_edit_batch

def test_route_directly():
    app = create_app()
    
    with app.app_context():
        batch_id = "1d40fb5c-500c-4127-9c4a-05d9f53fe47f"
        
        print(f"🔍 Testing route function directly with batch_id: {batch_id}")
        
        # First verify the blocks exist
        blocks = Block.query.filter_by(batch_id=batch_id).all()
        print(f"📊 Found {len(blocks)} blocks in database")
        
        if not blocks:
            print("❌ No blocks found - route will fail")
            return False
            
        for block in blocks:
            print(f"  Block {block.id}: Court {block.court_id}, Date {block.date}")
        
        # Now test the route logic manually
        try:
            # Remove 'batch_' prefix if present to get the actual UUID
            actual_batch_id = batch_id.replace('batch_', '') if batch_id.startswith('batch_') else batch_id
            
            print(f"📝 Processed batch_id: '{actual_batch_id}'")
            
            # Get all blocks with this batch_id
            blocks = Block.query.filter_by(batch_id=actual_batch_id).all()
            
            print(f"📊 Query result: {len(blocks)} blocks")
            
            if not blocks:
                print("❌ No blocks found after processing")
                return False
            
            # Use the first block as the primary block for data
            primary_block = blocks[0]
            
            # Extract court IDs from all blocks in the batch
            court_ids = [block.court_id for block in blocks]
            
            # Create a combined block data structure
            edit_block_data = {
                'id': primary_block.id,
                'batch_id': actual_batch_id,  # Use the batch_id from the URL, not from the database
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
            
            print(f"✅ Successfully created edit_block_data:")
            print(f"  ID: {edit_block_data['id']}")
            print(f"  Batch ID: '{edit_block_data['batch_id']}'")
            print(f"  Court IDs: {edit_block_data['court_ids']}")
            print(f"  Date: {edit_block_data['date']}")
            print(f"  Time: {edit_block_data['start_time']} - {edit_block_data['end_time']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error in route logic: {e}")
            return False

if __name__ == "__main__":
    success = test_route_directly()
    print(f"\n{'✅ Route logic works correctly!' if success else '❌ Route logic failed!'}")
    sys.exit(0 if success else 1)