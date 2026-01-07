# Debug Scripts Archive

This directory contains archived debug scripts from the project's development history.

## Purpose

These scripts were created during development to troubleshoot specific issues. They are kept here for historical reference but are **not part of the active codebase**.

## Contents

### Booking/Reservation Debug Scripts
- `debug_booking.py` - Debug booking functionality
- `debug_booking_issue.py` - Troubleshoot specific booking issues
- `debug_booking_simple.py` - Simplified booking debugging
- `debug_blocks.py` - Debug time block functionality

### Form Debug Scripts
- `debug_form_initialization.py` - Debug form initialization
- `debug_form_simple.py` - Simplified form debugging

### Route/Query Debug Scripts
- `debug_actual_route.py` - Debug actual route handling
- `debug_batch_query.py` - Debug batch query performance
- `debug_browser_html.py` - Debug HTML rendering in browser

### Security Debug Scripts
- `manual_security_validation.py` - Manual security testing

## Important Notes

⚠️ **These scripts are NOT maintained:**
- May not work with current codebase
- May use outdated imports or APIs
- May reference removed functionality
- Kept for reference only

## Using These Scripts

If you need to debug similar issues:

1. **Don't use these directly** - they may be outdated
2. **Use as reference** - understand the debugging approach
3. **Create new scripts** - based on current codebase
4. **Use proper debugging tools:**
   - Flask debug mode with breakpoints
   - Logging (`app.logger`)
   - Database query logging
   - Browser developer tools

## Better Debugging Approaches

### For Database Issues
```python
# Enable SQLAlchemy query logging in config.py
SQLALCHEMY_ECHO = True
```

### For Forms
```python
# In your route
if form.errors:
    app.logger.error(f"Form errors: {form.errors}")
```

### For Route Testing
```bash
# Use Flask's test client
python -m pytest tests/ -v
```

### For Browser Issues
- Use browser DevTools (F12)
- Check Network tab for requests
- Check Console for JavaScript errors

## Cleanup

These scripts may be deleted in the future if:
- Similar issues don't recur
- Better debugging methods are established
- Scripts become too outdated to be useful

For now, they're archived here as historical documentation of past debugging efforts.
