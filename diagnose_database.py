#!/usr/bin/env python3
"""
Diagnostic script to check database state and identify issues
"""

import os
import sys
import psycopg2
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
        print("❌ No database URL found.")
        return None
    
    try:
        # Parse the PostgreSQL URL properly
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

def diagnose_database():
    """Diagnose database issues"""
    
    print("🔍 Database Diagnostic Tool")
    print("=" * 50)
    
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        print("✓ Database connection successful")
        
        with conn.cursor() as cursor:
            # 1. Check what tables exist
            print("\n📋 Step 1: Checking existing tables...")
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = cursor.fetchall()
            print(f"Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table[0]}")
            
            # 2. Check for active connections and locks
            print("\n🔒 Step 2: Checking for active connections and locks...")
            cursor.execute("""
                SELECT pid, usename, state, wait_event_type, wait_event, 
                       query_start, state_change, query
                FROM pg_stat_activity 
                WHERE datname = current_database()
                AND state != 'idle'
                ORDER BY query_start DESC
            """)
            active_connections = cursor.fetchall()
            
            if active_connections:
                print(f"Found {len(active_connections)} active connections:")
                for conn_info in active_connections:
                    pid, user, state, wait_type, wait_event, start_time, change_time, query = conn_info
                    print(f"  - PID {pid} ({user}): {state}")
                    if wait_type:
                        print(f"    Waiting for: {wait_type} - {wait_event}")
                    if query:
                        print(f"    Query: {query[:100]}...")
            else:
                print("✓ No active connections found")
            
            # 3. Check for locks on tables
            print("\n🔐 Step 3: Checking for table locks...")
            cursor.execute("""
                SELECT l.pid, l.mode, l.granted, t.relname, a.usename, a.query
                FROM pg_locks l
                JOIN pg_class t ON l.relation = t.oid
                JOIN pg_stat_activity a ON l.pid = a.pid
                WHERE t.relkind = 'r'
                AND t.relname = 'order'
                ORDER BY l.pid
            """)
            locks = cursor.fetchall()
            
            if locks:
                print(f"Found {len(locks)} locks on 'order' table:")
                for lock in locks:
                    pid, mode, granted, table, user, query = lock
                    status = "GRANTED" if granted else "WAITING"
                    print(f"  - PID {pid} ({user}): {mode} - {status}")
                    if query:
                        print(f"    Query: {query[:100]}...")
            else:
                print("✓ No locks found on 'order' table")
            
            # 4. Try a simple query on the order table with timeout
            print("\n🧪 Step 4: Testing order table access...")
            try:
                # Set a statement timeout
                cursor.execute("SET statement_timeout = '5s'")
                
                print("  - Attempting SELECT COUNT(*) FROM \"order\"...")
                cursor.execute("SELECT COUNT(*) FROM \"order\"")
                count = cursor.fetchone()[0]
                print(f"✓ Success! Order table has {count} records")
                
            except psycopg2.extensions.QueryCanceledError:
                print("❌ Query timed out after 5 seconds")
                print("💡 The order table is likely locked or has issues")
                return False
            except Exception as e:
                print(f"❌ Error accessing order table: {e}")
                return False
            
            # 5. Check table structure
            print("\n📊 Step 5: Checking order table structure...")
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'order'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            print(f"Order table has {len(columns)} columns:")
            for col in columns:
                name, data_type, nullable, default = col
                print(f"  - {name} ({data_type}) {'NULL' if nullable == 'YES' else 'NOT NULL'}")
                if default:
                    print(f"    DEFAULT: {default}")
            
            # 6. Check for commission columns specifically
            commission_cols = [col for col in columns if 'commission' in col[0].lower()]
            if commission_cols:
                print(f"\n✅ Commission columns already exist:")
                for col in commission_cols:
                    print(f"  - {col[0]} ({col[1]})")
            else:
                print("\n❌ No commission columns found")
        
        print("\n✅ Database diagnostic completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Diagnostic error: {e}")
        return False
    finally:
        if conn:
            conn.close()
            print("🔌 Database connection closed")

if __name__ == "__main__":
    success = diagnose_database()
    
    if not success:
        print("\n💡 Recommendations:")
        print("1. If the order table is locked, try:")
        print("   - Restarting your Flask application")
        print("   - Checking for long-running queries")
        print("2. If the table has issues, consider:")
        print("   - Renaming 'order' to 'orders' to avoid reserved keyword")
        print("   - Recreating the table structure")
        sys.exit(1)
    else:
        print("\n🎉 Database is healthy and ready for modifications!") 