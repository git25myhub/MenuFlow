#!/usr/bin/env python3
"""
Database migration script to add commission columns to the order table
"""

import os
import sys
from sqlalchemy import text

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_migration():
    """Run the migration to add commission columns"""
    
    try:
        # Import after setting up the path
        from app import app, db
        
        with app.app_context():
            print("Starting commission columns migration...")
            
            # Get the database connection
            connection = db.engine.connect()
            
            # Check if columns already exist
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'order' 
                AND column_name IN ('commission_amount', 'commission_status')
            """))
            
            existing_columns = [row[0] for row in result.fetchall()]
            print(f"Existing commission columns: {existing_columns}")
            
            # Add commission_amount if it doesn't exist
            if 'commission_amount' not in existing_columns:
                print("Adding commission_amount column...")
                connection.execute(text("""
                    ALTER TABLE "order" 
                    ADD COLUMN commission_amount FLOAT DEFAULT 0.0
                """))
                print("✓ commission_amount column added")
            else:
                print("✓ commission_amount column already exists")
            
            # Add commission_status if it doesn't exist
            if 'commission_status' not in existing_columns:
                print("Adding commission_status column...")
                connection.execute(text("""
                    ALTER TABLE "order" 
                    ADD COLUMN commission_status VARCHAR(20) DEFAULT 'pending'
                """))
                print("✓ commission_status column added")
            else:
                print("✓ commission_status column already exists")
            
            # Commit the transaction
            connection.commit()
            connection.close()
            
            print("\n✅ Migration completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    run_migration() 