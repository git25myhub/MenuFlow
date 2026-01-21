#!/usr/bin/env python3
"""
Direct PostgreSQL script to add commission columns to the order table
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import time
from urllib.parse import urlparse

def get_database_connection():
    """Get database connection from environment or config"""
    # Try to get from environment variables first
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        # Try to get from config file
        try:
            from app import app
            database_url = app.config.get('SQLALCHEMY_DATABASE_URI')
        except:
            pass
    
    if not database_url:
        print("❌ No database URL found. Please set DATABASE_URL environment variable.")
        return None
    
    try:
        # Parse the PostgreSQL URL properly
        if database_url.startswith('postgresql://'):
            # Use urllib.parse to properly handle the URL
            parsed = urlparse(database_url)
            
            # Extract components
            username = parsed.username
            password = parsed.password
            host = parsed.hostname
            port = parsed.port or 5432
            database = parsed.path.lstrip('/')  # Remove leading slash
            
            # Handle query parameters
            sslmode = 'require'  # Default for Render
            if parsed.query:
                # Parse query parameters
                query_params = dict(item.split('=') for item in parsed.query.split('&'))
                sslmode = query_params.get('sslmode', 'require')
            
            print(f"🔌 Connecting to: {host}:{port}/{database}")
            
            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=username,
                password=password,
                sslmode=sslmode,
                connect_timeout=10
            )
            return conn
        else:
            print("❌ Database URL must start with postgresql://")
            return None
            
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return None

def column_exists(conn, table_name, column_name):
    """Check if a column exists in the specified table"""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = %s 
                AND column_name = %s
            """, (table_name, column_name))
            return cursor.fetchone() is not None
    except Exception as e:
        print(f"⚠ Warning: Could not check if column exists: {e}")
        return False

def add_commission_columns():
    """Add commission columns to the order table"""
    
    print("🔌 Connecting to PostgreSQL database...")
    conn = get_database_connection()
    
    if not conn:
        return False
    
    try:
        print("✓ Database connection successful")
        
        # Test if we can read from the order table
        try:
            print("  - Testing order table access...")
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM \"order\" LIMIT 1")
                count = cursor.fetchone()[0]
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
        commission_amount_exists = column_exists(conn, "order", "commission_amount")
        commission_status_exists = column_exists(conn, "order", "commission_status")
        
        print(f"  - commission_amount exists: {commission_amount_exists}")
        print(f"  - commission_status exists: {commission_status_exists}")
        
        if commission_amount_exists and commission_status_exists:
            print("✅ All commission columns already exist!")
            return True
        
        print("\nStep 3: Adding commission columns...")
        
        with conn.cursor() as cursor:
            # Add commission_amount column if it doesn't exist
            if not commission_amount_exists:
                print("  - Adding commission_amount column...")
                try:
                    print("    - Executing ALTER TABLE for commission_amount...")
                    cursor.execute("""
                        ALTER TABLE "order" 
                        ADD COLUMN commission_amount FLOAT DEFAULT 0.0
                    """)
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
                    cursor.execute("""
                        ALTER TABLE "order" 
                        ADD COLUMN commission_status VARCHAR(20) DEFAULT 'pending'
                    """)
                    print("    ✓ commission_status column added successfully")
                except Exception as e:
                    print(f"    ❌ commission_status column error: {e}")
                    return False
            else:
                print("  - commission_status column already exists, skipping")
            
            # Commit the changes
            print("  - Committing changes...")
            try:
                conn.commit()
                print("    ✓ Changes committed successfully")
            except Exception as e:
                print(f"    ❌ Commit failed: {e}")
                return False
        
        print("\nStep 4: Verifying columns were added...")
        
        # Verify the columns exist by checking the table structure
        try:
            print("  - Running verification query...")
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name, data_type, column_default 
                    FROM information_schema.columns 
                    WHERE table_name = 'order' 
                    AND column_name IN ('commission_amount', 'commission_status')
                    ORDER BY column_name
                """)
                
                columns = cursor.fetchall()
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
    finally:
        if conn:
            conn.close()
            print("🔌 Database connection closed")

if __name__ == "__main__":
    print("Starting commission columns addition (direct PostgreSQL connection)...")
    print(f"Current working directory: {os.getcwd()}")
    
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