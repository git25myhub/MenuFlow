from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import User, MenuItem, Order, db, Restaurant

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://menu_db_0gl8_user:6bd16fRcM0t9XKH7CpzpL8r6gIZcSTlM@dpg-d5oj6kk9c44c738nd2eg-a.oregon-postgres.render.com/menu_db_0gl8?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

def migrate_users_to_restaurant():
    # Step 1: Create Restaurant entries for each unique restaurant_name
    unique_restaurants = db.session.query(User.restaurant_name, User.logo_url, User.currency).distinct().all()
    name_to_restaurant = {}
    for name, logo_url, currency in unique_restaurants:
        if not name:
            continue
        restaurant = Restaurant.query.filter_by(name=name).first()
        if not restaurant:
            restaurant = Restaurant(name=name, logo_url=logo_url, currency=currency)
            db.session.add(restaurant)
            db.session.commit()
        name_to_restaurant[name] = restaurant

    # Step 2: Update users to reference the new Restaurant
    users = User.query.all()
    for user in users:
        if user.restaurant_name in name_to_restaurant:
            user.restaurant_id = name_to_restaurant[user.restaurant_name].id
    db.session.commit()

if __name__ == "__main__":
    from app import app
    with app.app_context():
        migrate_users_to_restaurant()
        print("Migration complete: Users now reference Restaurant model.") 