#!/usr/bin/env python3
"""Debug the template rendering issue."""

import sys
sys.path.append('.')
from app import create_app, db
from app.models import Block
from flask import render_template_string

app = create_app()

with app.app_context():
    # Get the first block with batch_id
    block = Block.query.filter(Block.batch_id.isnot(None)).first()
    
    if not block:
        print("No blocks with batch_id found")
        sys.exit(1)
    
    # Simulate the exact template logic from court_blocking.html
    edit_block_data = {
        'id': block.id,
        'batch_id': block.batch_id,
        'court_ids': [block.court_id],
        'date': block.date,
        'start_time': block.start_time,
        'end_time': block.end_time,
        'reason_id': block.reason_id,
        'details': block.details,
        'related_block_ids': [block.id]
    }
    
    print(f"edit_block_data.batch_id = {edit_block_data['batch_id']}")
    print(f"Type: {type(edit_block_data['batch_id'])}")
    print(f"Bool value: {bool(edit_block_data['batch_id'])}")
    
    # Test the exact template logic
    template = '''
    <form id="multi-court-form" 
          data-edit-mode="{{ 'true' if edit_block_data else 'false' }}" 
          data-batch-id="{{ edit_block_data.batch_id if edit_block_data else '' }}" 
          data-block-id="{{ edit_block_data.id if edit_block_data else '' }}">
        <!-- Debug info -->
        <div>
            edit_block_data exists: {{ edit_block_data is not none }}
            batch_id value: "{{ edit_block_data.batch_id if edit_block_data else 'NO_DATA' }}"
            batch_id type: {{ edit_block_data.batch_id.__class__.__name__ if edit_block_data and edit_block_data.batch_id else 'None' }}
        </div>
    </form>
    '''
    
    rendered = render_template_string(template, edit_block_data=edit_block_data)
    print(f"Rendered template:\n{rendered}")
    
    # Also test with None value
    print("\n--- Testing with None batch_id ---")
    edit_block_data_none = edit_block_data.copy()
    edit_block_data_none['batch_id'] = None
    
    rendered_none = render_template_string(template, edit_block_data=edit_block_data_none)
    print(f"Rendered with None batch_id:\n{rendered_none}")