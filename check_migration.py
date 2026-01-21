from app import app, db
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
import os

def check_migration():
    with app.app_context():
        # Get the absolute path to the migrations directory and alembic.ini
        base_dir = os.path.dirname(os.path.abspath(__file__))
        migrations_dir = os.path.join(base_dir, 'migrations')
        alembic_ini = os.path.join(base_dir, 'alembic.ini')
        
        # Create Alembic configuration
        alembic_cfg = Config(alembic_ini)
        alembic_cfg.set_main_option('script_location', migrations_dir)
        alembic_cfg.set_main_option('sqlalchemy.url', str(db.engine.url))
        
        # Get the script directory
        script = ScriptDirectory.from_config(alembic_cfg)
        
        # Get current revision
        from alembic.runtime.migration import MigrationContext
        from sqlalchemy import inspect
        
        conn = db.engine.connect()
        context = MigrationContext.configure(conn)
        current_rev = context.get_current_revision()
        
        if current_rev:
            print(f"Current migration revision: {current_rev}")
        else:
            print("No migration revision found in the database.")

if __name__ == '__main__':
    check_migration() 