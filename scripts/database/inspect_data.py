#!/usr/bin/env python3
"""
Check the actual database being used by the Flask app
"""

import sqlite3
import os

def check_actual_database():
    # The actual database from .env file
    db_path = "instance/tennis_club.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return
    
    print(f"🔍 Connecting to ACTUAL database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Show all blocks
        cursor.execute("SELECT id, court_id, date, batch_id FROM block ORDER BY created_at DESC LIMIT 10;")
        blocks = cursor.fetchall()
        print(f"\n📋 Recent blocks in ACTUAL database (last 10):")
        for block in blocks:
            print(f"  ID: {block[0]}, Court: {block[1]}, Date: {block[2]}, Batch: {block[3]}")
        
        # Look for the specific batch_id
        batch_id = "1d40fb5c-500c-4127-9c4a-05d9f53fe47f"
        cursor.execute("SELECT * FROM block WHERE batch_id = ?", (batch_id,))
        specific_blocks = cursor.fetchall()
        
        print(f"\n🎯 Blocks with batch_id '{batch_id}' in ACTUAL database:")
        if specific_blocks:
            for block in specific_blocks:
                print(f"  Block ID: {block[0]}, Court: {block[1]}, Date: {block[2]}, Time: {block[3]}-{block[4]}")
        else:
            print("  ❌ No blocks found with this batch_id in ACTUAL database")
        
        # Show all unique batch_ids
        cursor.execute("SELECT DISTINCT batch_id FROM block ORDER BY batch_id;")
        batch_ids = cursor.fetchall()
        print(f"\n🔖 All batch_ids in ACTUAL database:")
        for batch in batch_ids:
            print(f"  {batch[0]}")
            
        # Count total blocks
        cursor.execute("SELECT COUNT(*) FROM block;")
        total_blocks = cursor.fetchone()[0]
        print(f"\n📊 Total blocks in ACTUAL database: {total_blocks}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_actual_database()