#!/usr/bin/env python3
"""
Check if the batch exists in the database
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Block

def check_batch():
    app = create_app()
    
    with app.app_context():
        batch_id = "1d40fb5c-500c-4127-9c4a-05d9f53fe47f"
        
        print(f"🔍 Checking for blocks with batch_id: {batch_id}")
        
        # Query for blocks with this batch_id
        blocks = Block.query.filter_by(batch_id=batch_id).all()
        
        print(f"📊 Found {len(blocks)} blocks with this batch_id")
        
        if blocks:
            for i, block in enumerate(blocks):
                print(f"  Block {i+1}:")
                print(f"    ID: {block.id}")
                print(f"    Court: {block.court_id}")
                print(f"    Date: {block.date}")
                print(f"    Time: {block.start_time} - {block.end_time}")
                print(f"    Batch ID: {block.batch_id}")
                print(f"    Reason ID: {block.reason_id}")
        else:
            print("❌ No blocks found with this batch_id")
            
            # Check if there are any blocks at all
            all_blocks = Block.query.limit(5).all()
            print(f"📊 Total blocks in database: {Block.query.count()}")
            
            if all_blocks:
                print("📝 Sample blocks:")
                for block in all_blocks:
                    print(f"  - ID: {block.id}, Batch: {block.batch_id}, Court: {block.court_id}")

if __name__ == "__main__":
    check_batch()