#!/usr/bin/env python3
"""
Recreate database from scratch.

WARNING: This will DELETE ALL DATA in the database!
Only use this for cleaning up development/production databases.

Usage:
    python recreate_database.py
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
from sqlalchemy import text

def recreate_database():
    """Drop all tables and recreate from models."""
    app = create_app('production')
    
    with app.app_context():
        print("=" * 60)
        print("Database Recreation Script")
        print("=" * 60)
        print()
        print("WARNING: This will DELETE ALL DATA in the database!")
        print()
        
        # Show current database
        database_url = app.config.get('SQLALCHEMY_DATABASE_URI')
        if database_url:
            # Hide password in display
            display_url = database_url
            if '@' in database_url:
                parts = database_url.split('@')
                user_pass = parts[0].split('//')[-1]
                if ':' in user_pass:
                    user = user_pass.split(':')[0]
                    display_url = database_url.replace(user_pass, f"{user}:****")
            print(f"Database: {display_url}")
        print()
        
        # Get confirmation
        response = input("Are you ABSOLUTELY SURE you want to continue? (type 'YES' to confirm): ").strip()
        
        if response != 'YES':
            print("Aborted.")
            return False
        
        print()
        print("Dropping all tables...")
        
        try:
            # Disable foreign key checks
            db.session.execute(text("SET FOREIGN_KEY_CHECKS=0"))
            
            # Get all table names
            result = db.session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
            """))
            
            tables = [row[0] for row in result]
            
            print(f"Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table}")
            print()
            
            # Drop all tables
            for table in tables:
                print(f"Dropping {table}...")
                db.session.execute(text(f"DROP TABLE IF EXISTS `{table}`"))
            
            # Re-enable foreign key checks
            db.session.execute(text("SET FOREIGN_KEY_CHECKS=1"))
            db.session.commit()
            
            print()
            print("✓ All tables dropped successfully!")
            print()
            
            # Create all tables from models
            print("Creating tables from models...")
            db.create_all()
            
            print()
            print("✓ All tables created successfully!")
            print()
            
            # Show created tables
            result = db.session.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]
            
            print(f"Created {len(tables)} tables:")
            for table in sorted(tables):
                print(f"  - {table}")
            
            print()
            print("=" * 60)
            print("Database recreation complete!")
            print("=" * 60)
            print()
            print("Next steps:")
            print("  1. Create initial migration: flask db stamp head")
            print("  2. Or if you have migrations: flask db upgrade")
            print("  3. Create admin user and seed data as needed")
            print()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error: {e}")
            return False

if __name__ == '__main__':
    success = recreate_database()
    sys.exit(0 if success else 1)
