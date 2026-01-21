from flask_login import UserMixin
from extensions import db
import json
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timezone
UTC = timezone.utc  # Compatibility alias for Python < 3.11
from sqlalchemy.orm import relationship

# Restaurant Model
class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    logo_url = db.Column(db.String(255), nullable=True)
    currency = db.Column(db.String(10), default='USD')
    description = db.Column(db.Text, nullable=True)
    address = db.Column(db.String(255), nullable=True)
    opening_hours = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    social_media = db.Column(db.String(255), nullable=True)
    contact_phone = db.Column(db.String(50), nullable=True)
    help_contact = db.Column(db.String(50), nullable=True)
    mpesa_number = db.Column(db.String(20), nullable=True)
    payment_method = db.Column(db.String(20), default='manual')
    mpesa_receiving_method = db.Column(db.String(20), nullable=True)
    mpesa_paybill = db.Column(db.String(20), nullable=True)
    mpesa_till = db.Column(db.String(20), nullable=True)
    mpesa_phone_receiver = db.Column(db.String(20), nullable=True)
    theme_color = db.Column(db.String(7), default='#e67e22')
    menu_layout = db.Column(db.String(50), default='list')
    show_prices = db.Column(db.Boolean, default=True)
    show_descriptions = db.Column(db.Boolean, default=True)
    language = db.Column(db.String(10), default='en')
    timezone = db.Column(db.String(50), default='UTC')
    users = relationship('User', back_populates='restaurant')

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    admin_panel_password_hash = db.Column(db.String(128), nullable=True)  # For admin panel secondary password
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=True)
    restaurant = relationship('Restaurant', back_populates='users')
    # Remove restaurant_name, logo_url, currency, etc. from here in the future
    restaurant_name = db.Column(db.String(120), nullable=False)
    logo_url = db.Column(db.String(255), nullable=True)
    qr_url = db.Column(db.String(255), nullable=True)
    currency = db.Column(db.String(10), default='USD')
    restaurant_description = db.Column(db.Text, nullable=True)
    restaurant_address = db.Column(db.String(255), nullable=True)
    opening_hours = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    social_media = db.Column(db.String(255), nullable=True)
    contact_phone = db.Column(db.String(50), nullable=True)
    help_contact = db.Column(db.String(50), nullable=True)
    mpesa_number = db.Column(db.String(20), nullable=True)
    payment_method = db.Column(db.String(20), default='manual')
    mpesa_receiving_method = db.Column(db.String(20), nullable=True)
    mpesa_paybill = db.Column(db.String(20), nullable=True)
    mpesa_till = db.Column(db.String(20), nullable=True)
    mpesa_phone_receiver = db.Column(db.String(20), nullable=True)
    theme_color = db.Column(db.String(7), default='#e67e22')
    menu_layout = db.Column(db.String(50), default='list')
    show_prices = db.Column(db.Boolean, default=True)
    show_descriptions = db.Column(db.Boolean, default=True)
    language = db.Column(db.String(10), default='en')
    timezone = db.Column(db.String(50), default='UTC')
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default='staff')
    orders = db.relationship('Order', backref='user', lazy=True, foreign_keys='Order.user_id')


    def check_password(self, password):
        return check_password_hash(self.password, password)



    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    @staticmethod
    def create_admin(email, password):
        """Create an admin user if it doesn't exist"""
        admin = User.query.filter_by(email=email).first()
        if not admin:
            admin = User(
                email=email,
                password=generate_password_hash(password, method='pbkdf2:sha256'),
                restaurant_name='System Administrator',
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
        return admin

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    menu_items = db.relationship('MenuItem', backref='category', lazy=True)

# Update MenuItem to include category_id
class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    stock = db.Column(db.Integer, default=0) # Add stock column

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('menu_items', lazy=True))

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)


# Order Model
class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    name = db.Column(db.String(120), nullable=False)

    order = db.relationship('Order', backref=db.backref('order_items', lazy=True))
    menu_item = db.relationship('MenuItem', backref=db.backref('order_items', lazy=True))

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.String(50), nullable=True)
    items = db.Column(db.Text, nullable=False)  # JSON string of items, quantities, prices
    special_instructions = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Added restaurant_id as nullable
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='new') # e.g., 'new', 'pending', 'paid', 'delivered', 'cancelled'
    customer_name = db.Column(db.String(120), nullable=True)
    customer_phone = db.Column(db.String(50), nullable=True) # E.164 format
    delivery_address = db.Column(db.Text, nullable=True)
    order_type = db.Column(db.String(50), default='dine_in') # 'dine_in' or 'delivery'
    # Archiving
    is_archived = db.Column(db.Boolean, default=False)
    archived_at = db.Column(db.DateTime, nullable=True)
    
    # Commission fields
    commission_amount = db.Column(db.Float, default=0.0)
    commission_status = db.Column(db.String(20), default='pending')  # 'pending', 'calculated', 'paid'
    
    # Indexes
    __table_args__ = (
        db.Index('idx_order_customer_phone', 'customer_phone', 'created_at'),
        db.Index('idx_order_duplicate_detection', 'restaurant_id', 'customer_name', 'customer_phone', 'delivery_address', 'order_type', 'table_number', 'total_amount', 'created_at'),
        db.Index('idx_order_restaurant_created', 'restaurant_id', 'created_at'),
    )

    # Set restaurant_id to user_id when creating new orders
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.restaurant_id and self.user_id:
            self.restaurant_id = self.user_id

    def calculate_commission(self):
        """Calculate commission for this order"""
        config = CommissionConfig.query.filter_by(
            restaurant_id=self.restaurant_id, 
            is_active=True
        ).first()
        
        if not config:
            return 0.0
            
        if self.total_amount < config.minimum_order_amount:
            return 0.0
            
        if config.commission_type == 'percentage':
            commission = (self.total_amount * config.commission_rate) / 100
        else:
            commission = config.commission_rate
            
        if config.maximum_commission:
            commission = min(commission, config.maximum_commission)
            
        return round(commission, 2)

    def get_commission_rate(self):
        """Get the commission rate used for this order"""
        config = CommissionConfig.query.filter_by(
            restaurant_id=self.restaurant_id, 
            is_active=True
        ).first()
        return config.commission_rate if config else 0.0

    def get_commission_type(self):
        """Get the commission type used for this order"""
        config = CommissionConfig.query.filter_by(
            restaurant_id=self.restaurant_id, 
            is_active=True
        ).first()
        return config.commission_type if config else 'percentage'

# Commission System Models

class CommissionConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    commission_type = db.Column(db.String(20), default='percentage')  # 'percentage' or 'fixed'
    commission_rate = db.Column(db.Float, nullable=False)  # Percentage (e.g., 5.0) or fixed amount
    minimum_order_amount = db.Column(db.Float, default=0.0)  # Minimum order for commission
    maximum_commission = db.Column(db.Float, nullable=True)  # Cap on commission amount
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    restaurant = db.relationship('User', backref='commission_configs')

class CommissionTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_amount = db.Column(db.Float, nullable=False)
    commission_amount = db.Column(db.Float, nullable=False)
    commission_rate_used = db.Column(db.Float, nullable=False)
    commission_type = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'paid', 'cancelled'
    payment_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    order = db.relationship('Order', backref='commission_transactions')
    restaurant = db.relationship('User', backref='commission_transactions')

class CommissionBill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    total_commission = db.Column(db.Float, nullable=False)
    orders_count = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'partially_paid', 'paid', 'overdue'
    due_date = db.Column(db.DateTime, nullable=False)
    paid_date = db.Column(db.DateTime, nullable=True)
    payment_reference = db.Column(db.String(100), nullable=True)
    amount_received = db.Column(db.Float, default=0.0)
    confirmed_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    restaurant = db.relationship(
        'User', backref='commission_bills', foreign_keys=[restaurant_id]
    )
    confirmed_by_user = db.relationship('User', foreign_keys=[confirmed_by_user_id])

class CommissionPayout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    transaction_count = db.Column(db.Integer, nullable=False)
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'processed', 'paid'
    payment_method = db.Column(db.String(50), nullable=True)
    payment_reference = db.Column(db.String(100), nullable=True)
    processed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    restaurant = db.relationship('User', backref='commission_payouts')

class HelpInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    other = db.Column(db.Text, nullable=True)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('feedbacks', lazy=True))

class DarajaCredentials(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    consumer_key = db.Column(db.String(255), nullable=False)
    consumer_secret = db.Column(db.String(255), nullable=False)
    shortcode = db.Column(db.String(20), nullable=False)
    passkey = db.Column(db.String(255), nullable=False)
    environment = db.Column(db.String(20), default='production')  # 'production' or 'sandbox'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('daraja_credentials', lazy=True))
    
    def __repr__(self):
        return f'<DarajaCredentials {self.id} for User {self.user_id}>'

class PlatformSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    callback_url_sandbox = db.Column(db.String(255), nullable=True)
    callback_url_production = db.Column(db.String(255), nullable=True)
    # Commission platform settings
    platform_mpesa_number = db.Column(db.String(20), default='254769950059')
    platform_commission_rate = db.Column(db.Float, default=5.0)  # Default 5%
    commission_currency = db.Column(db.String(10), default='KES')

class PendingPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_token = db.Column(db.String(64), unique=True, nullable=False)
    order_data = db.Column(db.Text, nullable=False)  # JSON string
    phone = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_paid = db.Column(db.Boolean, default=False)

# Notification System Models
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), default='info')  # 'info', 'warning', 'success', 'error', 'update', 'feature'
    priority = db.Column(db.String(20), default='normal')  # 'low', 'normal', 'high', 'urgent'
    is_global = db.Column(db.Boolean, default=False)  # Global notifications for all restaurants
    target_restaurant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Specific restaurant
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Admin who created it
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)  # Optional expiration
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    target_restaurant = db.relationship('User', foreign_keys=[target_restaurant_id], backref='targeted_notifications')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_notifications')

class NotificationRead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    notification_id = db.Column(db.Integer, db.ForeignKey('notification.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    read_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    notification = db.relationship('Notification', backref='read_by_users')
    user = db.relationship('User', backref='read_notifications')
    
    # Ensure one read record per user per notification
    __table_args__ = (db.UniqueConstraint('notification_id', 'user_id', name='unique_notification_read'),)



