#!/usr/bin/env python3
"""
Create notification system tables in the database.
This script adds the Notification and NotificationRead tables to support the notification bell system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Notification, NotificationRead

def create_notification_tables():
    """Create notification tables in the database."""
    with app.app_context():
        try:
            # Create the notification tables
            db.create_all()
            print("✅ Notification tables created successfully!")
            
            # Verify tables exist
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'notification' in tables and 'notification_read' in tables:
                print("✅ Tables verified in database:")
                print(f"   - notification: {tables.count('notification')} found")
                print(f"   - notification_read: {tables.count('notification_read')} found")
            else:
                print("❌ Tables not found in database")
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ Error creating notification tables: {e}")
            return False

if __name__ == "__main__":
    print("🔔 Creating notification system tables...")
    success = create_notification_tables()
    
    if success:
        print("\n🎉 Notification system tables created successfully!")
        print("You can now use the notification bell system.")
    else:
        print("\n💥 Failed to create notification tables.")
        sys.exit(1)
