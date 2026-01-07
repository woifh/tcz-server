#!/usr/bin/env python3
"""Debug what's actually being rendered in the browser."""

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
    
    # Simulate the exact backend route logic
    batch_id = block.batch_id
    actual_batch_id = batch_id.replace('batch_', '') if batch_id.startswith('batch_') else batch_id
    
    blocks = Block.query.filter_by(batch_id=actual_batch_id).all()
    primary_block = blocks[0]
    court_ids = [block.court_id for block in blocks]
    
    edit_block_data = {
        'id': primary_block.id,
        'batch_id': actual_batch_id,
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
    
    print(f"Backend data:")
    print(f"  edit_block_data['batch_id'] = {repr(edit_block_data['batch_id'])}")
    print(f"  type = {type(edit_block_data['batch_id'])}")
    print(f"  bool = {bool(edit_block_data['batch_id'])}")
    
    # Test the template rendering with a request context
    with app.test_request_context():
        try:
            # Render just the form tag part
            from flask import render_template_string
            
            form_template = '''
            <form id="multi-court-form" 
                  data-edit-mode="{{ 'true' if edit_block_data else 'false' }}" 
                  data-block-id="{{ edit_block_data.id if edit_block_data else '' }}" 
                  data-batch-id="{{ edit_block_data.batch_id if (edit_block_data and edit_block_data.batch_id and edit_block_data.batch_id != 'None' and edit_block_data.batch_id != 'null') else '' }}">
            '''
            
            rendered = render_template_string(form_template, edit_block_data=edit_block_data)
            print(f"\\nRendered form tag:")
            print(rendered)
            
            # Extract attributes
            import re
            edit_mode_match = re.search(r'data-edit-mode="([^"]*)"', rendered)
            batch_id_match = re.search(r'data-batch-id="([^"]*)"', rendered)
            block_id_match = re.search(r'data-block-id="([^"]*)"', rendered)
            
            print(f"\\nExtracted attributes:")
            if edit_mode_match:
                print(f"  data-edit-mode: '{edit_mode_match.group(1)}'")
            if batch_id_match:
                print(f"  data-batch-id: '{batch_id_match.group(1)}'")
            if block_id_match:
                print(f"  data-block-id: '{block_id_match.group(1)}'")
                
            # Test with None batch_id to see what happens
            print(f"\\n--- Testing with None batch_id ---")
            edit_block_data_none = edit_block_data.copy()
            edit_block_data_none['batch_id'] = None
            
            rendered_none = render_template_string(form_template, edit_block_data=edit_block_data_none)
            print(f"Rendered with None: {rendered_none}")
            
            batch_id_match_none = re.search(r'data-batch-id="([^"]*)"', rendered_none)
            if batch_id_match_none:
                print(f"  data-batch-id with None: '{batch_id_match_none.group(1)}'")
                
        except Exception as e:
            print(f"Template rendering error: {e}")
            import traceback
            traceback.print_exc()