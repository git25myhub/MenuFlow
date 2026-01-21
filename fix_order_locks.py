#!/usr/bin/env python3
"""
Script to fix order table locks and add commission columns
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse

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

def kill_blocking_processes(conn):
    """Kill processes that are blocking the order table"""
    print("🔪 Step 1: Killing blocking processes...")
    
    with conn.cursor() as cursor:
        # Find processes that are waiting for locks on the order table
        cursor.execute("""
            SELECT DISTINCT l.pid, a.usename, a.query
            FROM pg_locks l
            JOIN pg_class t ON l.relation = t.oid
            JOIN pg_stat_activity a ON l.pid = a.pid
            WHERE t.relname = 'order'
            AND l.granted = false
            AND a.pid != pg_backend_pid()
        """)
        
        blocking_pids = cursor.fetchall()
        
        if not blocking_pids:
            print("✓ No blocking processes found")
            return True
        
        print(f"Found {len(blocking_pids)} blocking processes:")
        for pid, user, query in blocking_pids:
            print(f"  - PID {pid} ({user}): {query[:50]}...")
        
        # Kill the blocking processes
        for pid, user, query in blocking_pids:
            try:
                print(f"  - Terminating PID {pid}...")
                cursor.execute("SELECT pg_terminate_backend(%s)", (pid,))
                result = cursor.fetchone()[0]
                if result:
                    print(f"    ✓ Successfully terminated PID {pid}")
                else:
                    print(f"    ⚠ Failed to terminate PID {pid}")
            except Exception as e:
                print(f"    ❌ Error terminating PID {pid}: {e}")
        
        conn.commit()
        return True

def kill_idle_transactions(conn):
    """Kill idle transactions that might be holding locks"""
    print("\n🔪 Step 2: Killing idle transactions...")
    
    with conn.cursor() as cursor:
        # Find idle transactions
        cursor.execute("""
            SELECT pid, usename, query_start, state, query
            FROM pg_stat_activity
            WHERE state = 'idle in transaction'
            AND pid != pg_backend_pid()
            AND query_start < NOW() - INTERVAL '5 minutes'
        """)
        
        idle_pids = cursor.fetchall()
        
        if not idle_pids:
            print("✓ No long-running idle transactions found")
            return True
        
        print(f"Found {len(idle_pids)} idle transactions:")
        for pid, user, start_time, state, query in idle_pids:
            print(f"  - PID {pid} ({user}): {state} since {start_time}")
        
        # Kill the idle transactions
        for pid, user, start_time, state, query in idle_pids:
            try:
                print(f"  - Terminating idle PID {pid}...")
                cursor.execute("SELECT pg_terminate_backend(%s)", (pid,))
                result = cursor.fetchone()[0]
                if result:
                    print(f"    ✓ Successfully terminated PID {pid}")
                else:
                    print(f"    ⚠ Failed to terminate PID {pid}")
            except Exception as e:
                print(f"    ❌ Error terminating PID {pid}: {e}")
        
        conn.commit()
        return True

def add_commission_columns(conn):
    """Add commission columns to the order table"""
    print("\n📝 Step 3: Adding commission columns...")
    
    with conn.cursor() as cursor:
        # Check if columns already exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'order' 
            AND column_name IN ('commission_amount', 'commission_status')
        """)
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        if 'commission_amount' in existing_columns and 'commission_status' in existing_columns:
            print("✅ Commission columns already exist!")
            return True
        
        # Add commission_amount column if it doesn't exist
        if 'commission_amount' not in existing_columns:
            print("  - Adding commission_amount column...")
            try:
                cursor.execute("""
                    ALTER TABLE "order" 
                    ADD COLUMN commission_amount FLOAT DEFAULT 0.0
                """)
                print("    ✓ commission_amount column added")
            except Exception as e:
                print(f"    ❌ Error adding commission_amount: {e}")
                return False
        
        # Add commission_status column if it doesn't exist
        if 'commission_status' not in existing_columns:
            print("  - Adding commission_status column...")
            try:
                cursor.execute("""
                    ALTER TABLE "order" 
                    ADD COLUMN commission_status VARCHAR(20) DEFAULT 'pending'
                """)
                print("    ✓ commission_status column added")
            except Exception as e:
                print(f"    ❌ Error adding commission_status: {e}")
                return False
        
        # Commit the changes
        conn.commit()
        print("    ✓ Changes committed successfully")
        
        # Verify the columns were added
        cursor.execute("""
            SELECT column_name, data_type, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'order' 
            AND column_name IN ('commission_amount', 'commission_status')
            ORDER BY column_name
        """)
        
        columns = cursor.fetchall()
        print("\nVerification - Added columns:")
        for col in columns:
            print(f"  - {col[0]} ({col[1]}) DEFAULT {col[2]}")
        
        return True

def fix_order_table():
    """Main function to fix order table locks and add columns"""
    print("🔧 Order Table Lock Fix Tool")
    print("=" * 50)
    
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        print("✓ Database connection successful")
        
        # Step 1: Kill blocking processes
        if not kill_blocking_processes(conn):
            return False
        
        # Step 2: Kill idle transactions
        if not kill_idle_transactions(conn):
            return False
        
        # Step 3: Add commission columns
        if not add_commission_columns(conn):
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
    success = fix_order_table()
    
    if success:
        print("\n🎉 All operations completed successfully!")
    else:
        print("\n💥 Operations failed!")
        sys.exit(1) 