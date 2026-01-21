from app import app, db
from models import User, MenuItem, Order, HelpInfo, Feedback, DarajaCredentials, PlatformSettings

with app.app_context():
    print("Dropping all tables...")
    db.drop_all()
    print("All tables dropped successfully")
    
    print("Creating all tables...")
    db.create_all()
    print("All tables created successfully")
    
    # Create admin user if needed
    admin_email = "stephenngariadmin@gmail.com"
    admin_password = "@Myadmin05"
    
    admin = User.query.filter_by(email=admin_email).first()
    if not admin:
        print("Creating admin user...")
        admin = User(
            email=admin_email,
            password=generate_password_hash(admin_password, method='pbkdf2:sha256'),
            restaurant_name='System Administrator',
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Admin user created with email: {admin_email} and password: {admin_password}")
    else:
        print("Admin user already exists")

print("Database reset completed successfully!")
