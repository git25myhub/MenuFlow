#!/usr/bin/env python3
"""
Check database status and locks
"""

import os
import sys
import sqlite3
import time

# Add the current directory to Python path to import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_database_status():
    """Check if the database is accessible and not locked"""
    
    db_path = 'database.db'
    
    print("🔍 Checking database status...")
    print(f"Database file: {db_path}")
    print(f"File exists: {os.path.exists(db_path)}")
    
    if os.path.exists(db_path):
        print(f"File size: {os.path.getsize(db_path)} bytes")
        print(f"Last modified: {time.ctime(os.path.getmtime(db_path))}")
    
    try:
        # Try to connect to the database
        print("\n📡 Testing database connection...")
        conn = sqlite3.connect(db_path, timeout=10.0)
        print("✓ Database connection successful")
        
        # Check if we can read from the order table
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM \"order\"")
            count = cursor.fetchone()[0]
            print(f"✓ Order table accessible, contains {count} records")
        except Exception as e:
            print(f"⚠ Warning: Could not read from order table: {e}")
        
        # Check table structure
        try:
            cursor.execute("PRAGMA table_info(\"order\")")
            columns = cursor.fetchall()
            print(f"\n📋 Order table has {len(columns)} columns:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]}) DEFAULT {col[4]}")
        except Exception as e:
            print(f"⚠ Could not get table structure: {e}")
        
        # Check for commission columns
        commission_cols = [col for col in columns if 'commission' in col[1].lower()]
        if commission_cols:
            print(f"\n✅ Commission columns already exist:")
            for col in commission_cols:
                print(f"  - {col[1]} ({col[2]}) DEFAULT {col[4]}")
        else:
            print("\n❌ No commission columns found - they need to be added")
        
        conn.close()
        print("\n✅ Database is accessible and ready for modifications")
        return True
        
    except sqlite3.OperationalError as e:
        print(f"❌ Database locked or inaccessible: {e}")
        return False
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    success = check_database_status()
    if not success:
        print("\n💡 Suggestions:")
        print("1. Close any other applications using the database")
        print("2. Restart your Flask application if it's running")
        print("3. Check if any other Python scripts are accessing the database")
        sys.exit(1)
    else:
        print("\n🚀 Database is ready! You can now run add_order_columns.py") 