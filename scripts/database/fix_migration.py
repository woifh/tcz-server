#!/usr/bin/env python3
"""
Fix migration version mismatch on PythonAnywhere.

This script updates the alembic_version table to match the current
migration files, fixing the "Can't locate revision" error.

Usage:
    python fix_migration_version.py
"""
import sys
import os
from pathlib import Path

# Load production environment variables before importing app
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / '.env.production'
    if env_file.exists():
        print(f"Loading environment from: {env_file}")
        load_dotenv(env_file)
    else:
        print("Warning: .env.production not found, using default .env")
        load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed")

from app import create_app, db

def fix_migration_version():
    """Update alembic_version to the current migration."""
    # Ensure we're using production config
    app = create_app('production')

    with app.app_context():
        # Current migration version in migrations/versions/
        current_version = '7347717de84b'

        print("=" * 60)
        print("Migration Version Fix Script")
        print("=" * 60)
        print()

        # Check current version in database
        try:
            result = db.session.execute(
                db.text("SELECT version_num FROM alembic_version")
            ).fetchone()

            if result:
                old_version = result[0]
                print(f"Current database version: {old_version}")
            else:
                print("No version found in database (fresh database)")
                old_version = None
        except Exception as e:
            print(f"Could not read current version: {e}")
            print("This might be a fresh database.")
            old_version = None

        print(f"Target migration version: {current_version}")
        print()

        if old_version == current_version:
            print("✓ Database is already at the correct version!")
            return True

        # Confirm before proceeding
        print("This will update the alembic_version table to match")
        print("the current migration files.")
        print()
        response = input("Do you want to proceed? (yes/no): ").strip().lower()

        if response != 'yes':
            print("Aborted.")
            return False

        try:
            # Delete old version
            if old_version:
                db.session.execute(db.text("DELETE FROM alembic_version"))

            # Insert new version
            db.session.execute(
                db.text("INSERT INTO alembic_version (version_num) VALUES (:version)"),
                {"version": current_version}
            )
            db.session.commit()

            print()
            print("✓ Migration version updated successfully!")
            print()
            print("Next steps:")
            print("  1. The database schema should already match the current models")
            print("  2. If you've added new columns/tables, you may need to run:")
            print("     flask db migrate -m 'description'")
            print("     flask db upgrade")
            print()
            return True

        except Exception as e:
            db.session.rollback()
            print(f"✗ Error updating version: {e}")
            return False

if __name__ == '__main__':
    success = fix_migration_version()
    sys.exit(0 if success else 1)
