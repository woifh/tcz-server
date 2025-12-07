# Member Name Field Migration Guide

## Overview

The Member model has been updated to use separate `firstname` and `lastname` fields instead of a single `name` field.

## Changes Made

### 1. Model Changes (`app/models.py`)
- ✅ Changed `name` field to `firstname` and `lastname`
- ✅ Added `@property name` for backward compatibility (returns "firstname lastname")
- ✅ Updated ordering to use `lastname, firstname`

### 2. Service Changes (`app/services/member_service.py`)
- ✅ Updated `search_members()` to search both `firstname` and `lastname`
- ✅ Changed ordering to `lastname, firstname`

### 3. Route Changes (`app/routes/members.py`)
- ✅ Updated member creation to use `firstname` and `lastname`
- ✅ Updated member update to handle both fields
- ✅ Changed validation messages

### 4. CLI Changes (`app/cli.py`)
- ✅ Updated `create-admin` command to prompt for firstname and lastname

### 5. Init Script Changes (`init_db.py`)
- ✅ Updated admin creation to use firstname and lastname

### 6. Test Fixtures (`tests/conftest.py`)
- ✅ Updated `test_member` and `test_admin` fixtures

## Remaining Work

### Test Files Need Manual Update

The following test files contain `Member(name=...)` that need to be converted to `Member(firstname=..., lastname=...)`:

1. `tests/test_member_service.py` - Partially done, needs completion
2. `tests/test_member_routes.py`
3. `tests/test_admin_routes.py`
4. `tests/test_auth.py`
5. `tests/test_models.py`
6. `tests/test_email_service.py`
7. `tests/test_templates.py`
8. `tests/test_members.py`
9. `tests/test_validation_service.py`
10. `tests/test_reservation_routes.py`

### Conversion Helper Scripts

Two scripts have been created to help with conversion:

1. **`convert_names_to_fields.py`** - Interactive Python script
   ```bash
   python convert_names_to_fields.py tests/test_member_service.py
   ```

2. **`batch_convert_tests.sh`** - Batch conversion script (macOS/Linux)
   ```bash
   chmod +x batch_convert_tests.sh
   ./batch_convert_tests.sh
   ```

### Manual Conversion Pattern

For each test file, replace:

```python
# OLD
member = Member(name="John Doe", email="john@example.com", role="member")

# NEW
member = Member(firstname="John", lastname="Doe", email="john@example.com", role="member")
```

For variables:
```python
# OLD
member = Member(name=member_name, email=email, role="member")

# NEW  
# Split the name first
firstname, lastname = member_name.split(maxsplit=1)
member = Member(firstname=firstname, lastname=lastname, email=email, role="member")

# OR use the helper function
from tests.test_helpers import split_name
firstname, lastname = split_name(member_name)
member = Member(firstname=firstname, lastname=lastname, email=email, role="member")
```

## Database Migration

**IMPORTANT**: Since you said "no migration needed", this assumes you're working with a fresh database or will manually update the database schema.

If you need to migrate existing data:

1. **Add new columns** to the `member` table:
   ```sql
   ALTER TABLE member ADD COLUMN firstname VARCHAR(50);
   ALTER TABLE member ADD COLUMN lastname VARCHAR(50);
   ```

2. **Migrate existing data** (split name into firstname/lastname):
   ```sql
   UPDATE member 
   SET firstname = SUBSTRING_INDEX(name, ' ', 1),
       lastname = SUBSTRING_INDEX(name, ' ', -1);
   ```

3. **Make columns NOT NULL**:
   ```sql
   ALTER TABLE member MODIFY firstname VARCHAR(50) NOT NULL;
   ALTER TABLE member MODIFY lastname VARCHAR(50) NOT NULL;
   ```

4. **Drop old column**:
   ```sql
   ALTER TABLE member DROP COLUMN name;
   ```

5. **Update indexes**:
   ```sql
   DROP INDEX idx_member_name ON member;
   CREATE INDEX idx_member_firstname ON member(firstname);
   CREATE INDEX idx_member_lastname ON member(lastname);
   ```

## Testing

After making changes, run tests to verify:

```bash
# Run all tests
python3 -m pytest

# Run specific test files
python3 -m pytest tests/test_member_service.py -v
python3 -m pytest tests/test_member_routes.py -v

# Run search-related tests
python3 -m pytest tests/test_member_service.py::TestMemberServiceSearch -v
```

## Frontend Changes Needed

The frontend JavaScript also needs updates:

### Files to Update:
1. **`app/static/js/member-search.js`** - Already uses `member.name` property (should work)
2. **`app/templates/favourites.html`** - Uses `fav.name` (should work with property)
3. **Any admin forms** - Need to update to have separate firstname/lastname inputs

### Admin Form Example:

```html
<!-- OLD -->
<input type="text" name="name" placeholder="Name" required>

<!-- NEW -->
<input type="text" name="firstname" placeholder="Vorname" required>
<input type="text" name="lastname" placeholder="Nachname" required>
```

## Backward Compatibility

The `@property name` in the Member model provides backward compatibility:

```python
@property
def name(self):
    """Return full name for backward compatibility."""
    return f"{self.firstname} {self.lastname}"
```

This means:
- ✅ `member.name` still works in templates
- ✅ `member.name` still works in JavaScript
- ✅ Existing code that reads `name` continues to work
- ❌ Code that tries to SET `member.name = "..."` will fail

## Deployment Checklist

Before deploying to PythonAnywhere:

- [ ] Update all test files
- [ ] Run full test suite locally
- [ ] Update database schema (if using existing database)
- [ ] Update any admin forms to use firstname/lastname
- [ ] Test member creation through UI
- [ ] Test member search functionality
- [ ] Verify member display in all pages

## Quick Test

To quickly test if the changes work:

```python
from app import create_app, db
from app.models import Member

app = create_app()
with app.app_context():
    # Create a test member
    member = Member(firstname="John", lastname="Doe", email="john@test.com", role="member")
    member.set_password("test123")
    db.session.add(member)
    db.session.commit()
    
    # Test the name property
    print(f"Full name: {member.name}")  # Should print: John Doe
    print(f"First: {member.firstname}, Last: {member.lastname}")
```

## Need Help?

If you encounter issues:
1. Check the test output for specific errors
2. Review the conversion scripts
3. Use `git diff` to see what changed
4. Restore from backups if needed: `mv file.bak file`
