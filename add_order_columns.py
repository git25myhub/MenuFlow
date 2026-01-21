#!/usr/bin/env python3
"""
Simple script to add commission columns to the order table using Flask app context
"""

import os
import sys
import time

# Add the current directory to Python path to import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, TimeoutError

def column_exists(table_name, column_name):
    """Check if a column exists in the specified table"""
    try:
        with db.engine.connect() as connection:
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = :table_name 
                AND column_name = :column_name
            """), {"table_name": table_name, "column_name": column_name})
            return result.fetchone() is not None
    except Exception as e:
        print(f"⚠ Warning: Could not check if column exists: {e}")
        return False

def add_commission_columns():
    """Add commission columns to the order table using Flask app context"""
    
    with app.app_context():
        try:
            print("Step 1: Testing database connection...")
            
            # Test connection first
            with db.engine.connect() as connection:
                print("✓ Database connection successful")
                
                # Test if we can read from the order table
                try:
                    print("  - Testing order table access...")
                    result = connection.execute(text("SELECT COUNT(*) FROM \"order\" LIMIT 1"))
                    count = result.fetchone()[0]
                    print(f"✓ Order table accessible, contains {count} records")
                        
                except Exception as e:
                    print(f"⚠ Warning: Could not read from order table: {e}")
                    print("💡 This might be due to:")
                    print("   1. Table lock from another process")
                    print("   2. Reserved keyword 'order' causing issues")
                    print("   3. Permission problems")
                    return False
            
            print("\nStep 2: Checking existing columns...")
            
            # Check if columns already exist
            commission_amount_exists = column_exists("order", "commission_amount")
            commission_status_exists = column_exists("order", "commission_status")
            
            print(f"  - commission_amount exists: {commission_amount_exists}")
            print(f"  - commission_status exists: {commission_status_exists}")
            
            if commission_amount_exists and commission_status_exists:
                print("✅ All commission columns already exist!")
                return True
            
            print("\nStep 3: Adding commission columns...")
            
            # Use SQLAlchemy 2.0 compatible text() and execute() method
            with db.engine.connect() as connection:
                # Add commission_amount column if it doesn't exist
                if not commission_amount_exists:
                    print("  - Adding commission_amount column...")
                    try:
                        print("    - Executing ALTER TABLE for commission_amount...")
                        connection.execute(text("""
                            ALTER TABLE "order" 
                            ADD COLUMN commission_amount FLOAT DEFAULT 0.0
                        """))
                        print("    ✓ commission_amount column added successfully")
                    except Exception as e:
                        print(f"    ❌ commission_amount column error: {e}")
                        return False
                else:
                    print("  - commission_amount column already exists, skipping")
                
                # Add commission_status column if it doesn't exist
                if not commission_status_exists:
                    print("  - Adding commission_status column...")
                    try:
                        print("    - Executing ALTER TABLE for commission_status...")
                        connection.execute(text("""
                            ALTER TABLE "order" 
                            ADD COLUMN commission_status VARCHAR(20) DEFAULT 'pending'
                        """))
                        print("    ✓ commission_status column added successfully")
                    except Exception as e:
                        print(f"    ❌ commission_status column error: {e}")
                        return False
                else:
                    print("  - commission_status column already exists, skipping")
                
                # Commit the changes
                print("  - Committing changes...")
                try:
                    connection.commit()
                    print("    ✓ Changes committed successfully")
                except Exception as e:
                    print(f"    ❌ Commit failed: {e}")
                    return False
            
            print("\nStep 4: Verifying columns were added...")
            
            # Verify the columns exist by checking the table structure
            with db.engine.connect() as connection:
                try:
                    print("  - Running verification query...")
                    result = connection.execute(text("""
                        SELECT column_name, data_type, column_default 
                        FROM information_schema.columns 
                        WHERE table_name = 'order' 
                        AND column_name IN ('commission_amount', 'commission_status')
                        ORDER BY column_name
                    """))
                    
                    columns = result.fetchall()
                    print("\nVerification - Added columns:")
                    if columns:
                        for col in columns:
                            print(f"  - {col[0]} ({col[1]}) DEFAULT {col[2]}")
                    else:
                        print("  ⚠ No commission columns found in verification query")
                        return False
                        
                except Exception as e:
                    print(f"❌ Verification failed: {e}")
                    return False
            
            print("\n✅ Commission columns successfully added to order table!")
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print(f"Error type: {type(e).__name__}")
            return False

if __name__ == "__main__":
    print("Starting commission columns addition...")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Database file exists: {os.path.exists('database.db')}")
    print(f"Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')[:50]}...")
    
    success = add_commission_columns()
    
    if success:
        print("\n🎉 Script completed successfully!")
    else:
        print("\n💥 Script failed!")
        print("\n💡 Troubleshooting tips:")
        print("1. Check if another process is using the database:")
        print("   SELECT pid, usename, state, query FROM pg_stat_activity WHERE datname = 'your_db_name';")
        print("2. Try running the query manually in psql:")
        print("   SELECT COUNT(*) FROM \"order\";")
        print("3. Consider renaming the table to avoid reserved keyword issues:")
        print("   ALTER TABLE \"order\" RENAME TO orders;")
        sys.exit(1) 