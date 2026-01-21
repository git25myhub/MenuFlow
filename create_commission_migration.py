#!/usr/bin/env python3
"""
Create Alembic migration for commission columns
"""

import os
import sys
from alembic import command
from alembic.config import Config

# Add the current directory to Python path to import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def create_commission_migration():
    """Create a migration for the commission columns"""
    
    with app.app_context():
        # Get the absolute path to the migrations directory and alembic.ini
        base_dir = os.path.dirname(os.path.abspath(__file__))
        migrations_dir = os.path.join(base_dir, 'migrations')
        alembic_ini = os.path.join(base_dir, 'alembic.ini')
        
        # Create Alembic configuration
        alembic_cfg = Config(alembic_ini)
        alembic_cfg.set_main_option('script_location', migrations_dir)
        alembic_cfg.set_main_option('sqlalchemy.url', str(db.engine.url))
        
        print("📝 Creating migration for commission columns...")
        
        try:
            # Create a new migration
            command.revision(
                alembic_cfg,
                message="Add commission columns to order table",
                autogenerate=True
            )
            
            print("✅ Migration created successfully!")
            print("\n💡 Next steps:")
            print("1. Review the generated migration file in migrations/versions/")
            print("2. Run 'python apply_migration.py' to apply the migration")
            print("3. Or run 'flask db upgrade' if using Flask-Migrate")
            
        except Exception as e:
            print(f"❌ Error creating migration: {e}")
            return False
        
        return True

if __name__ == "__main__":
    success = create_commission_migration()
    
    if not success:
        sys.exit(1) 