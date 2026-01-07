#!/usr/bin/env python3
"""Script to manually fix the unique_booking constraint issue."""
import os
from app import create_app, db

app = create_app('production')

with app.app_context():
    print("="*80)
    print("🔧 FIXING UNIQUE_BOOKING CONSTRAINT")
    print("="*80)
    
    # Get the database connection
    connection = db.engine.raw_connection()
    cursor = connection.cursor()
    
    try:
        # First, let's see what constraints exist
        print("\n📋 Current constraints on reservation table:")
        cursor.execute("""
            SELECT CONSTRAINT_NAME, CONSTRAINT_TYPE 
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
            WHERE TABLE_NAME = 'reservation' 
            AND TABLE_SCHEMA = DATABASE()
        """)
        constraints = cursor.fetchall()
        for constraint in constraints:
            print(f"  - {constraint[0]} ({constraint[1]})")
        
        # Check indexes
        print("\n📋 Current indexes on reservation table:")
        cursor.execute("SHOW INDEX FROM reservation")
        indexes = cursor.fetchall()
        for idx in indexes:
            print(f"  - {idx[2]} (Column: {idx[4]}, Unique: {idx[1] == 0})")
        
        # Try to drop the unique constraint
        print("\n🔨 Attempting to drop unique_booking constraint...")
        try:
            cursor.execute("ALTER TABLE reservation DROP INDEX unique_booking")
            connection.commit()
            print("✅ Successfully dropped unique_booking constraint!")
        except Exception as e:
            print(f"❌ Failed to drop constraint: {e}")
            connection.rollback()
            
            # If it fails, try alternative approach
            print("\n🔨 Trying alternative approach: recreate table without constraint...")
            print("⚠️  This is a more complex operation. Proceeding with caution...")
            
            # This would require recreating the table, which is risky
            # Instead, let's just show what needs to be done manually
            print("\n💡 Manual fix required:")
            print("   Run this SQL command directly in MySQL console:")
            print("   ")
            print("   ALTER TABLE reservation DROP INDEX unique_booking;")
            print("   ")
            print("   If that fails, you may need to:")
            print("   1. Check foreign key constraints")
            print("   2. Temporarily disable foreign key checks")
            print("   3. Drop and recreate the constraint")
        
        # Show final state
        print("\n📋 Final indexes on reservation table:")
        cursor.execute("SHOW INDEX FROM reservation")
        indexes = cursor.fetchall()
        for idx in indexes:
            print(f"  - {idx[2]} (Column: {idx[4]}, Unique: {idx[1] == 0})")
            
    finally:
        cursor.close()
        connection.close()
    
    print("\n" + "="*80)
