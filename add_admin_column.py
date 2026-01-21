import psycopg2
from werkzeug.security import generate_password_hash
import os
from dotenv import load_dotenv
load_dotenv()
def add_admin_column():
    # Get database URL from environment or use default
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://menu_db_sowe_user:8zV2EBJYnGNJUh8xg5NcycaU6O5WHeAp@dpg-d3f8ctemcj7s73e76vlg-a.oregon-postgres.render.com/menu_db_sowe?sslmode=require')
    
    # Connect to the database
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    try:
        # Add is_admin column
        cur.execute('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE')
        
        # Check if admin user exists
        cur.execute("SELECT id FROM \"user\" WHERE email = 'stephenngariadmin@gmail.com'")
        admin = cur.fetchone()
        
        if not admin:
            # Create admin user
            hashed_password = generate_password_hash('@Myadmin05', method='pbkdf2:sha256')
            cur.execute(
                """
                INSERT INTO "user" (email, password, restaurant_name, is_admin)
                VALUES (%s, %s, %s, %s)
                """,
                ('stephenngariadmin@gmail.com', hashed_password, 'System Administrator', True)
            )
        else:
            # Update existing user to be admin
            cur.execute(
                "UPDATE \"user\" SET is_admin = TRUE WHERE email = 'stephenngariadmin@gmail.com'"
            )
        
        # Commit the changes
        conn.commit()
        print("Admin column added and admin user created/updated successfully!")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    add_admin_column() 