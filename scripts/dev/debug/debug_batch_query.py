#!/usr/bin/env python3
"""
Debug the batch query to see what's happening
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Block

def debug_batch_query():
    app = create_app()
    
    with app.app_context():
        batch_id = "1d40fb5c-500c-4127-9c4a-05d9f53fe47f"
        
        print(f"🔍 Debugging batch query for: {batch_id}")
        print(f"📊 Batch ID type: {type(batch_id)}")
        print(f"📊 Batch ID length: {len(batch_id)}")
        
        # First, let's see all blocks and their batch_ids
        all_blocks = Block.query.all()
        print(f"\n📝 All blocks in database ({len(all_blocks)} total):")
        
        for block in all_blocks:
            print(f"  Block {block.id}:")
            print(f"    Court: {block.court_id}")
            print(f"    Date: {block.date}")
            print(f"    Batch ID: '{block.batch_id}' (type: {type(block.batch_id)}, len: {len(block.batch_id) if block.batch_id else 'None'})")
            print(f"    Batch ID repr: {repr(block.batch_id)}")
            
            # Check if this matches our target
            if block.batch_id == batch_id:
                print(f"    ✅ MATCHES target batch_id!")
            else:
                print(f"    ❌ Does not match target")
                
        print(f"\n🔍 Now testing the exact query:")
        
        # Test the exact query from the route
        blocks = Block.query.filter_by(batch_id=batch_id).all()
        print(f"📊 Query result: {len(blocks)} blocks found")
        
        if blocks:
            for block in blocks:
                print(f"  Found block: {block.id}, Court: {block.court_id}")
        else:
            print("❌ No blocks found with exact query")
            
            # Try some variations
            print("\n🔍 Trying variations:")
            
            # Try with string comparison
            blocks_like = Block.query.filter(Block.batch_id.like(f"%{batch_id}%")).all()
            print(f"📊 LIKE query result: {len(blocks_like)} blocks")
            
            # Try case insensitive
            blocks_ilike = Block.query.filter(Block.batch_id.ilike(batch_id)).all()
            print(f"📊 ILIKE query result: {len(blocks_ilike)} blocks")

if __name__ == "__main__":
    debug_batch_query()