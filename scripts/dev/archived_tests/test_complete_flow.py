#!/usr/bin/env python3
"""Test the complete edit flow."""

import sys
sys.path.append('.')
from app import create_app, db
from app.models import Block
from flask import render_template

app = create_app()

with app.app_context():
    # Get the first block with batch_id
    block = Block.query.filter(Block.batch_id.isnot(None)).first()
    
    if not block:
        print("No blocks with batch_id found")
        sys.exit(1)
    
    print(f"Testing complete flow for batch_id: {block.batch_id}")
    
    # Simulate the backend route logic exactly
    batch_id = block.batch_id
    actual_batch_id = batch_id.replace('batch_', '') if batch_id.startswith('batch_') else batch_id
    
    # Get all blocks with this batch_id
    blocks = Block.query.filter_by(batch_id=actual_batch_id).all()
    
    if not blocks:
        print('No blocks found for batch_id')
        sys.exit(1)
    
    # Use the first block as the primary block for data
    primary_block = blocks[0]
    
    # Extract court IDs from all blocks in the batch
    court_ids = [block.court_id for block in blocks]
    
    # Create a combined block data structure (exactly like the backend)
    edit_block_data = {
        'id': primary_block.id,
        'batch_id': actual_batch_id,  # Use the batch_id from the URL, not from the database
        'court_ids': court_ids,
        'date': primary_block.date,
        'start_time': primary_block.start_time,
        'end_time': primary_block.end_time,
        'reason_id': primary_block.reason_id,
        'details': primary_block.details,
        'created_by': primary_block.created_by,
        'created_at': primary_block.created_at,
        'related_block_ids': [block.id for block in blocks]
    }
    
    print(f'Backend edit_block_data: {edit_block_data}')
    
    # Test template rendering
    try:
        # This will test the actual template
        with app.test_request_context():
            rendered_html = render_template('admin/court_blocking.html', edit_block_data=edit_block_data)
            
            # Extract the form attributes
            import re
            form_match = re.search(r'<form[^>]*id=\"multi-court-form\"[^>]*>', rendered_html)
            
            if form_match:
                form_tag = form_match.group(0)
                print(f'Form tag: {form_tag}')
                
                # Extract data attributes
                edit_mode_match = re.search(r'data-edit-mode=\"([^\"]*)"', form_tag)
                batch_id_match = re.search(r'data-batch-id=\"([^\"]*)"', form_tag)
                block_id_match = re.search(r'data-block-id=\"([^\"]*)"', form_tag)
                
                if edit_mode_match:
                    print(f'data-edit-mode: \"{edit_mode_match.group(1)}\"')
                
                if batch_id_match:
                    print(f'data-batch-id: \"{batch_id_match.group(1)}\"')
                    
                    if batch_id_match.group(1) == actual_batch_id:
                        print('✅ Batch ID is correctly set in the template!')
                    else:
                        print(f'❌ Batch ID mismatch. Expected: {actual_batch_id}, Found: {batch_id_match.group(1)}')
                else:
                    print('❌ data-batch-id not found in form tag')
                
                if block_id_match:
                    print(f'data-block-id: \"{block_id_match.group(1)}\"')
            else:
                print('❌ Form tag not found in rendered HTML')
                
    except Exception as e:
        print(f'Error rendering template: {e}')
        import traceback
        traceback.print_exc()