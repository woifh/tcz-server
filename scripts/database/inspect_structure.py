#!/usr/bin/env python3
"""
Check the structure and data in the actual database
"""

import sqlite3
import os

def check_db_structure():
    db_path = "instance/tennis_club.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return
    
    print(f"🔍 Checking structure of ACTUAL database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Show all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"\n📊 Tables in ACTUAL database:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check each important table
        important_tables = ['member', 'block_reason', 'block', 'court']
        
        for table_name in important_tables:
            if any(t[0] == table_name for t in tables):
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                print(f"\n📋 {table_name} table: {count} records")
                
                if count > 0 and count < 10:  # Show a few records if not too many
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
                    records = cursor.fetchall()
                    for record in records:
                        print(f"  {record}")
            else:
                print(f"\n❌ {table_name} table: NOT FOUND")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_db_structure()