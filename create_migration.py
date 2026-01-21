from app import app, db
from alembic import command
from alembic.config import Config
import os

def create_migration():
    with app.app_context():
        # Get the absolute path to the migrations directory and alembic.ini
        base_dir = os.path.dirname(os.path.abspath(__file__))
        migrations_dir = os.path.join(base_dir, 'migrations')
        alembic_ini = os.path.join(base_dir, 'alembic.ini')
        
        # Create Alembic configuration
        alembic_cfg = Config(alembic_ini)
        alembic_cfg.set_main_option('script_location', migrations_dir)
        alembic_cfg.set_main_option('sqlalchemy.url', str(db.engine.url))
        
        # Generate the migration
        command.revision(alembic_cfg, 
                        message="initial schema",
                        autogenerate=True)
        print("Migration has been created successfully!")

if __name__ == '__main__':
    create_migration() 