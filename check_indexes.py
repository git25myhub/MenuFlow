#!/usr/bin/env python3
"""
Check existing indexes on the order table
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse

# Add the current directory to Python path to import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app

def get_database_connection():
    """Get database connection from environment or config"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        try:
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

def check_order_indexes():
    """Check existing indexes on the order table"""
    print("🔍 Checking indexes on order table...")
    
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            # Check all indexes on the order table using the correct query
            cursor.execute("""
                SELECT 
                    indexname,
                    indexdef
                FROM pg_indexes 
                WHERE tablename = 'order'
                ORDER BY indexname
            """)
            
            indexes = cursor.fetchall()
            
            if not indexes:
                print("❌ No indexes found on order table")
                return False
            
            print(f"✅ Found {len(indexes)} indexes on order table:")
            print("-" * 80)
            
            for index in indexes:
                indexname, indexdef = index
                print(f"📋 {indexname}")
                print(f"   Definition: {indexdef}")
                print()
            
            # Also check for any missing indexes that were mentioned in the migration
            missing_indexes = [
                'idx_order_customer_phone',
                'idx_order_duplicate_detection', 
                'idx_order_restaurant_created'
            ]
            
            existing_index_names = [idx[0] for idx in indexes]
            actually_missing = [idx for idx in missing_indexes if idx not in existing_index_names]
            
            if actually_missing:
                print("⚠️  Missing indexes that were mentioned in migration:")
                for idx in actually_missing:
                    print(f"   - {idx}")
            else:
                print("✅ All mentioned indexes still exist in database")
            
            return True
            
    except Exception as e:
        print(f"❌ Error checking indexes: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    with app.app_context():
        check_order_indexes() 