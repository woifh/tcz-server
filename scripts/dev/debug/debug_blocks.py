#!/usr/bin/env python3
"""Debug script to check block data and relationships."""

import sys
from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from app.models import Block, BlockReason
from datetime import date

def debug_blocks():
    """Check block data and relationships."""
    app = create_app('development')
    
    with app.app_context():
        print("=== Block Debug Information ===")
        
        # Check total blocks
        total_blocks = Block.query.count()
        print(f"Total blocks in database: {total_blocks}")
        
        if total_blocks == 0:
            print("No blocks found - this might be the issue.")
            return
        
        # Check blocks for today
        today = date.today()
        today_blocks = Block.query.filter_by(date=today).all()
        print(f"Blocks for today ({today}): {len(today_blocks)}")
        
        # Check for blocks with missing reason_id
        blocks_no_reason = Block.query.filter(Block.reason_id.is_(None)).all()
        print(f"Blocks with missing reason_id: {len(blocks_no_reason)}")
        
        # Check available block reasons
        reasons = BlockReason.query.all()
        print(f"Available block reasons: {len(reasons)}")
        for reason in reasons:
            print(f"  - {reason.id}: {reason.name}")
        
        # Check a few sample blocks
        sample_blocks = Block.query.limit(5).all()
        print(f"\nSample blocks:")
        for block in sample_blocks:
            try:
                reason_name = block.reason  # This should trigger the property
                print(f"  Block {block.id}: Court {block.court_id}, Date {block.date}, Reason: {reason_name}")
            except Exception as e:
                print(f"  Block {block.id}: ERROR accessing reason - {e}")
        
        print("\n=== End Debug ===")

if __name__ == '__main__':
    try:
        debug_blocks()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()