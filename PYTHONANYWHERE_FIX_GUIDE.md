# PythonAnywhere Database Fix Guide

## Problem
After deployment, you're getting 500 errors when logged in. The issue is that the database migration encountered a "Duplicate column name 'firstname'" error because the PythonAnywhere database already has those columns but isn't marked at the correct migration version.

## Solution

### Quick Fix (Recommended)

Run this single command on PythonAnywhere:

```bash
cd ~/tcz && bash fix_pythonanywhere_db.sh
```

This will:
1. Stamp the database to the correct migration version (088504aa5508)
2. Apply the pending migration to add the `is_short_notice` column
3. Reload the webapp

### Manual Fix (if script doesn't work)

```bash
# 1. Navigate to project
cd ~/tcz

# 2. Activate virtual environment
source ~/.virtualenvs/tennisclub/bin/activate

# 3. Set Flask app
export FLASK_APP=wsgi.py

# 4. Check current migration status
flask db current

# 5. Stamp database to correct version
flask db stamp 088504aa5508

# 6. Apply pending migrations
flask db upgrade

# 7. Reload webapp
touch /var/www/woifh_pythonanywhere_com_wsgi.py
```

## What This Does

### Migration 088504aa5508
- Adds `firstname` and `lastname` columns to user table
- Your database already has these columns (that's why you got the duplicate error)
- Stamping tells Flask-Migrate "yes, this migration is already applied"

### Migration c97a5390ecac
- Adds `is_short_notice` BOOLEAN column to reservation table
- This is the migration that needs to be applied
- Required for the short notice booking feature to work

## Verification

After running the fix, test these:

1. **Login**: Should work without 500 errors
2. **Dashboard**: Should load correctly
3. **Court Availability API**: `https://woifh.pythonanywhere.com/courts/availability?date=2025-12-09`
4. **Reservations API**: `https://woifh.pythonanywhere.com/reservations/?format=json`
5. **Make a booking**: Should work and show orange background if within 15 minutes

## Troubleshooting

### If you still get 500 errors:

1. **Check error logs**:
   - Go to https://www.pythonanywhere.com/user/woifh/
   - Click on "Web" tab
   - Scroll down to "Log files"
   - Check the error log for details

2. **Verify database columns**:
   ```bash
   cd ~/tcz
   source ~/.virtualenvs/tennisclub/bin/activate
   python3 << EOF
   from app import create_app, db
   from app.models import User, Reservation
   
   app = create_app()
   with app.app_context():
       # Check User table columns
       print("User columns:", User.__table__.columns.keys())
       
       # Check Reservation table columns
       print("Reservation columns:", Reservation.__table__.columns.keys())
       
       # Verify is_short_notice exists
       if 'is_short_notice' in Reservation.__table__.columns.keys():
           print("✅ is_short_notice column exists")
       else:
           print("❌ is_short_notice column missing")
   EOF
   ```

3. **Check migration history**:
   ```bash
   flask db history
   ```

### If migration fails:

If `flask db upgrade` fails, you might need to manually add the column:

```bash
# Connect to MySQL console
mysql -u woifh -h woifh.mysql.pythonanywhere-services.com -p

# Use your database
USE woifh$tennisclub;

# Add the column manually
ALTER TABLE reservation ADD COLUMN is_short_notice BOOLEAN DEFAULT FALSE;

# Add the index
CREATE INDEX idx_reservation_short_notice ON reservation(is_short_notice);

# Exit
exit;
```

Then stamp to the latest migration:
```bash
flask db stamp head
touch /var/www/woifh_pythonanywhere_com_wsgi.py
```

## Why This Happened

The PythonAnywhere database was modified directly or had migrations applied out of order, so the actual database schema is ahead of what Flask-Migrate thinks it is. Stamping tells Flask-Migrate "the database is actually at this version" so it can correctly apply only the migrations that are truly missing.

## Prevention

To avoid this in the future:
1. Always use `flask db upgrade` for migrations
2. Never modify the database schema manually
3. Keep migration history in sync between local and production
4. Test migrations locally before deploying to production

---

**Created**: December 9, 2025
**Status**: Ready to run
