#!/usr/bin/env python3
"""
Script to add database indexes for better order duplicate detection performance
"""

from app import app, db
from sqlalchemy import text

def add_order_indexes():
    """Add indexes to improve order duplicate detection performance"""
    with app.app_context():
        try:
            # Add composite index for duplicate detection
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_order_duplicate_detection 
                ON "order" (restaurant_id, customer_name, customer_phone, delivery_address, order_type, table_number, total_amount, created_at)
            """))
            
            # Add index for restaurant orders
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_order_restaurant_created 
                ON "order" (restaurant_id, created_at DESC)
            """))
            
            # Add index for customer orders
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_order_customer_phone 
                ON "order" (customer_phone, created_at DESC)
            """))
            
            db.session.commit()
            print("✅ Database indexes added successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error adding indexes: {str(e)}")

if __name__ == "__main__":
    add_order_indexes() 