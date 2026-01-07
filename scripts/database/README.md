# Database Utility Scripts

This directory contains utilities for managing and inspecting the Tennis Club database.

## Available Scripts

### Data Management

#### `seed.py`
Populate the database with initial data (courts and optional admin user).

**Usage:**
```bash
python scripts/database/seed.py
```

**What it does:**
- Creates 6 courts (numbered 1-6)
- Optionally creates an admin user (prompts for credentials)
- Safe to run multiple times (checks for existing data)

**When to use:**
- After initial database setup
- After running `recreate.py`
- To add missing courts

---

#### `recreate.py`
**⚠️ DESTRUCTIVE** - Drops all tables and recreates from SQLAlchemy models.

**Usage:**
```bash
python scripts/database/recreate.py
```

**What it does:**
- Drops ALL database tables (requires "YES" confirmation)
- Recreates schema from models
- Resets alembic_version to current migration

**When to use:**
- Nuclear option when migrations are completely broken
- Development environment resets (NOT for production!)
- After major schema refactoring

**Warning:**
- This deletes ALL data permanently
- Use `fix_migration.py` instead for production migration issues
- Always backup production data first

---

#### `delete_reservations.py`
Delete all reservations from the database.

**Usage:**
```bash
python scripts/database/delete_reservations.py
```

**When to use:**
- Clearing test data
- Resetting the reservation schedule
- Development cleanup

---

### Database Inspection

#### `inspect_structure.py`
Display the database schema and table structures.

**Usage:**
```bash
python scripts/database/inspect_structure.py
```

**What it shows:**
- All tables in the database
- Column names, types, and constraints for each table
- Primary and foreign keys

---

#### `inspect_data.py`
Query and display actual data from database tables.

**Usage:**
```bash
python scripts/database/inspect_data.py
```

**What it shows:**
- Data from key tables (members, courts, reservations, etc.)
- Row counts
- Sample records

---

#### `explore.py`
Interactive database exploration tool.

**Usage:**
```bash
python scripts/database/explore.py
```

**What it does:**
- Provides interactive prompts for database queries
- Allows custom SQL queries
- Displays results in readable format

---

### Migration Management

#### `fix_migration.py`
Fix Alembic migration version mismatches.

**Usage:**
```bash
python scripts/database/fix_migration.py
```

**What it does:**
- Shows current database migration version
- Updates alembic_version table to match migration files
- Resolves "Can't locate revision" errors

**When to use:**
- After getting "Can't locate revision" error during deployment
- When database version doesn't match migration files
- After migration file reorganization

**Common scenario:**
```
Error: Can't locate revision identified by 'abc123'
→ Run: python scripts/database/fix_migration.py
```

---

## Common Workflows

### Fresh Database Setup
```bash
# 1. Create database tables
flask db upgrade

# 2. Seed initial data
python scripts/database/seed.py

# 3. Verify setup
python scripts/database/inspect_structure.py
```

### Fix Migration Issues (Production)
```bash
# 1. Check current migration
flask db current

# 2. Fix version mismatch
python scripts/database/fix_migration.py

# 3. Run pending migrations
flask db upgrade
```

### Development Reset
```bash
# ⚠️ Development only!

# 1. Recreate database
python scripts/database/recreate.py

# 2. Seed data
python scripts/database/seed.py

# 3. Verify
python scripts/database/inspect_data.py
```

### Database Inspection
```bash
# Check schema
python scripts/database/inspect_structure.py

# Check data
python scripts/database/inspect_data.py

# Interactive exploration
python scripts/database/explore.py
```

## Environment Configuration

All scripts automatically load the appropriate environment:
- **Local development:** Uses `.env`
- **Production:** Uses `.env.production` (when FLASK_CONFIG=production)

To force production mode:
```bash
FLASK_CONFIG=production python scripts/database/script.py
```

## Safety Features

### Confirmations
Scripts that modify data require explicit confirmation:
- `recreate.py` requires typing "YES" in uppercase
- `fix_migration.py` requires "yes" confirmation

### Environment Detection
- Scripts detect and display which environment/database they're using
- Production scripts explicitly load `.env.production`

### Dry-run Support
Some scripts support checking before making changes:
```bash
# Show what would be done without executing
flask db upgrade --sql
```

## Troubleshooting

### "Can't connect to database"
- Check `.env` or `.env.production` file exists
- Verify DATABASE_URL is correct
- Ensure database server is running

### "Permission denied" when running scripts
```bash
chmod +x scripts/database/*.py
```

### Script can't find app modules
Make sure you're running from project root:
```bash
cd ~/tcz
python scripts/database/script.py
```

## Related Documentation

- **Migration troubleshooting:** [docs/PYTHONANYWHERE_DEPLOYMENT.md](../../docs/PYTHONANYWHERE_DEPLOYMENT.md)
- **Database schema:** Run `inspect_structure.py`
- **Flask-Migrate docs:** https://flask-migrate.readthedocs.io/
