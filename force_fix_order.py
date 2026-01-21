#!/usr/bin/env python3
"""
Force fix order table by killing all processes and using a different approach
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse
import time

def get_database_connection():
    """Get database connection from environment or config"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        try:
            from app import app
            database_url = app.config.get('SQLALCHEMY_DATABASE_URI')
        except:
            pass
    
    if not database_url:
        print("❌ No database URL found.")
        return None
    
    try:
        if database_url.startswith('postgresql://'):
            parsed = urlparse(database_url)
            
            username = parsed.username
            password = parsed.password
            host = parsed.hostname
            port = parsed.port or 5432
            database = parsed.path.lstrip('/')
            
            sslmode = 'require'
            if parsed.query:
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

def force_kill_all_processes(conn):
    """Force kill all processes except the current one"""
    print("💀 Step 1: Force killing ALL processes...")
    
    with conn.cursor() as cursor:
        # Get all processes except the current one
        cursor.execute("""
            SELECT pid, usename, state, query
            FROM pg_stat_activity
            WHERE pid != pg_backend_pid()
            AND datname = current_database()
        """)
        
        all_processes = cursor.fetchall()
        
        if not all_processes:
            print("✓ No other processes found")
            return True
        
        print(f"Found {len(all_processes)} processes to terminate:")
        for pid, user, state, query in all_processes:
            print(f"  - PID {pid} ({user}): {state}")
        
        # Kill all processes
        for pid, user, state, query in all_processes:
            try:
                print(f"  - Force terminating PID {pid}...")
                cursor.execute("SELECT pg_terminate_backend(%s)", (pid,))
                result = cursor.fetchone()[0]
                if result:
                    print(f"    ✓ Successfully terminated PID {pid}")
                else:
                    print(f"    ⚠ Failed to terminate PID {pid}")
            except Exception as e:
                print(f"    ❌ Error terminating PID {pid}: {e}")
        
        conn.commit()
        
        # Wait a moment for processes to fully terminate
        print("  - Waiting 3 seconds for processes to terminate...")
        time.sleep(3)
        
        return True

def check_columns_exist(conn):
    """Check if commission columns already exist"""
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'order' 
            AND column_name IN ('commission_amount', 'commission_status')
        """)
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        return existing_columns

def add_columns_with_timeout(conn):
    """Add columns with timeout protection"""
    print("\n📝 Step 2: Adding commission columns with timeout...")
    
    existing_columns = check_columns_exist(conn)
    
    if 'commission_amount' in existing_columns and 'commission_status' in existing_columns:
        print("✅ Commission columns already exist!")
        return True
    
    with conn.cursor() as cursor:
        # Set a short timeout for the ALTER TABLE operations
        cursor.execute("SET statement_timeout = '30s'")
        
        # Add commission_amount column if it doesn't exist
        if 'commission_amount' not in existing_columns:
            print("  - Adding commission_amount column...")
            try:
                print("    - Executing ALTER TABLE for commission_amount...")
                cursor.execute("""
                    ALTER TABLE "order" 
                    ADD COLUMN commission_amount FLOAT DEFAULT 0.0
                """)
                print("    ✓ commission_amount column added")
            except psycopg2.extensions.QueryCanceledError:
                print("    ❌ Timeout while adding commission_amount column")
                return False
            except Exception as e:
                print(f"    ❌ Error adding commission_amount: {e}")
                return False
        
        # Add commission_status column if it doesn't exist
        if 'commission_status' not in existing_columns:
            print("  - Adding commission_status column...")
            try:
                print("    - Executing ALTER TABLE for commission_status...")
                cursor.execute("""
                    ALTER TABLE "order" 
                    ADD COLUMN commission_status VARCHAR(20) DEFAULT 'pending'
                """)
                print("    ✓ commission_status column added")
            except psycopg2.extensions.QueryCanceledError:
                print("    ❌ Timeout while adding commission_status column")
                return False
            except Exception as e:
                print(f"    ❌ Error adding commission_status: {e}")
                return False
        
        # Commit the changes
        print("  - Committing changes...")
        conn.commit()
        print("    ✓ Changes committed successfully")
        
        return True

def verify_columns(conn):
    """Verify that the columns were added"""
    print("\n🔍 Step 3: Verifying columns...")
    
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'order' 
            AND column_name IN ('commission_amount', 'commission_status')
            ORDER BY column_name
        """)
        
        columns = cursor.fetchall()
        
        if not columns:
            print("❌ No commission columns found!")
            return False
        
        print("✅ Commission columns found:")
        for col in columns:
            print(f"  - {col[0]} ({col[1]}) DEFAULT {col[2]}")
        
        return True

def force_fix_order_table():
    """Main function to force fix order table"""
    print("💀 Force Order Table Fix Tool")
    print("=" * 50)
    
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        print("✓ Database connection successful")
        
        # Step 1: Force kill all processes
        if not force_kill_all_processes(conn):
            return False
        
        # Step 2: Add columns with timeout
        if not add_columns_with_timeout(conn):
            return False
        
        # Step 3: Verify columns
        if not verify_columns(conn):
            return False
        
        print("\n✅ Order table fixed and commission columns added successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if conn:
            conn.close()
            print("🔌 Database connection closed")

if __name__ == "__main__":
    success = force_fix_order_table()
    
    if success:
        print("\n🎉 All operations completed successfully!")
    else:
        print("\n💥 Operations failed!")
        print("\n💡 If this still fails, consider:")
        print("1. Restarting your Flask application completely")
        print("2. Using a database migration tool like Alembic")
        print("3. Renaming the 'order' table to 'orders' to avoid reserved keyword issues")
        sys.exit(1) 