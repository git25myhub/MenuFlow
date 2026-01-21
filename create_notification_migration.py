#!/usr/bin/env python3
"""
Create Alembic migration for notification tables.
Run this script to generate a migration file for the notification system.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_migration():
    """Create migration for notification tables."""
    print("🔔 Creating migration for notification tables...")
    print("\nRun the following command to create the migration:")
    print("  flask db migrate -m 'Add notification system tables'")
    print("\nThen apply it with:")
    print("  flask db upgrade")
    print("\nOr run the quick setup script:")
    print("  python create_notification_tables.py")

if __name__ == "__main__":
    create_migration()

