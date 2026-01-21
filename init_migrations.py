from app import app, db
from flask_migrate import stamp
 
with app.app_context():
    # Stamp the current state as the initial migration
    stamp()
    print("Migration state has been stamped successfully!") 