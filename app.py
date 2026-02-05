# Imports
import os
import sys
# Flask and extensions
# Conditional monkey patching (only when running the app directly, not for CLI commands like migrations)
# Skip monkey patching when imported by Flask CLI to avoid SSL connection issues with psycopg2
# When Flask CLI runs, __name__ will be 'app' (module name), not '__main__'
# Only patch when running directly: python app.py
if __name__ == '__main__':
    # Conditional gevent monkey patching (only on non-Windows)
    if sys.platform != "win32":
        try:
            from gevent import monkey
            monkey.patch_all()
        except ImportError:
            pass  # Gevent not available
    else:
        # On Windows: skip eventlet monkey patching to avoid greendns/dnspython conflict
        # (causes "udp() got unexpected keyword argument 'ignore_errors'" and email DNS lookup failures).
        # Flask-SocketIO will use threading mode instead.
        pass

from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory, jsonify, session, Response, stream_with_context, abort, make_response, send_file
from sqlalchemy import select
from flask_socketio import SocketIO
from flask_socketio import join_room
from werkzeug.security import check_password_hash, generate_password_hash
from hardware_notifier import HardwareNotifier, NotificationType
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired
# Create a singleton notifier instance (simulation_mode=False for live hardware)
SIMULATION_MODE = os.environ.get('SIMULATION_MODE', 'false').lower() == 'true'
from hardware_notifier import get_hardware_notifier, cleanup_hardware_notifier
# Defer creating the notifier until after app and SocketIO are initialized to avoid gevent fork issues
hardware_notifier = None

def notify_hardware(order_data):
    """
    Enhanced hardware notification function with better error handling
    and support for multiple notification types.
    
    Args:
        order_data: Dictionary containing order information
    """
    try:
        # Lazily create the hardware notifier
        global hardware_notifier
        if hardware_notifier is None:
            hardware_notifier = get_hardware_notifier(simulation_mode=SIMULATION_MODE)
        notifier = hardware_notifier
        
        # Extract status and determine notification type
        status = order_data.get('status', '').lower()
        order_type = order_data.get('order_type', '').lower()
        
        # Map status to notification type
        notification_type = None
        priority = 1  # Default priority
        
        if status in ['new', 'created']:
            notification_type = NotificationType.NEW_ORDER
            priority = 3  # High priority for new orders
        elif status == 'ready':
            notification_type = NotificationType.ORDER_READY
            priority = 4  # Very high priority for ready orders
        elif status == 'delivered':
            notification_type = NotificationType.ORDER_DELIVERED
            priority = 2  # Medium priority for delivered orders
        elif status == 'paid' or status == 'payment_confirmed':
            notification_type = NotificationType.PAYMENT_RECEIVED
            priority = 3  # High priority for payments
        elif status == 'error' or status == 'failed':
            notification_type = NotificationType.ERROR
            priority = 5  # Highest priority for errors
        elif status == 'warning':
            notification_type = NotificationType.WARNING
            priority = 2  # Medium priority for warnings
        else:
            notification_type = NotificationType.INFO
            priority = 1  # Low priority for info
        
        # Add metadata for better tracking
        metadata = {
            'status': status,
            'order_type': order_type,
            'timestamp': datetime.now().isoformat(),
            'source': 'order_management'
        }
        
        # Queue the notification
        success = notifier.notify(notification_type, priority=priority, metadata=metadata)
        
        if success:
            app.logger.info(f"Hardware notification queued: {notification_type.value} (priority: {priority})")
        else:
            logger.warning(f"Failed to queue hardware notification: {notification_type.value}")
            
    except Exception as e:
        logger.error(f"Error in notify_hardware: {str(e)}")
        # Try to notify error on hardware if possible
        try:
            notifier = get_hardware_notifier(simulation_mode=SIMULATION_MODE)
            notifier.notify(NotificationType.ERROR, priority=5, metadata={'error': str(e)})
        except Exception as cleanup_error:
            logger.error(f"Failed to send error notification: {cleanup_error}")

import qrcode
from qrcode.constants import ERROR_CORRECT_H
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask_wtf.csrf import CSRFProtect, generate_csrf, validate_csrf
from flask_migrate import Migrate
import logging
logger = logging.getLogger(__name__)
import os
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

# Database and models
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import case, extract, func, update, text, and_
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import NoResultFound

# Commission service
from commission_service import CommissionService
import sqlalchemy

# Forms
from forms import LoginForm, ProfileForm, SettingsForm, MenuItemForm, DarajaCredentialsForm, PlatformSettingsForm, DeleteForm, AdminLoginForm, HelpInfoForm, FlaskForm, FeedbackForm, RegistrationForm, RegistrationVerificationForm, SetAdminPanelPasswordForm, AdminPanelPasswordForm, ChangeAdminPanelPasswordForm, ResetAdminPanelPasswordForm, PasswordResetRequestForm, PasswordResetForm

# Models
from models import User, MenuItem, Order, OrderItem, HelpInfo, Feedback, DarajaCredentials, PlatformSettings, Category, Restaurant, PendingPayment, CommissionTransaction, CommissionConfig, CommissionBill, CommissionPayout

# Utilities and third-party
import threading
import weakref
import time
import time as time_module
from threading import Timer
# Conditional gevent sleep import (only on non-Windows)
if sys.platform != "win32":
    from gevent import sleep as gevent_sleep
else:
    # On Windows, use time.sleep as fallback
    gevent_sleep = time.sleep
import requests
import json
import csv
import re
import calendar
import pytz
import io
from io import StringIO
from datetime import datetime, timedelta, time as datetime_time, timezone
UTC = timezone.utc  # Compatibility alias for Python < 3.11
from typing import Optional
from PIL import Image
from qrcode import QRCode
from qrcode.constants import ERROR_CORRECT_H
from fpdf import FPDF
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import cloudinary.api
from mpesa_utils import stk_push
import traceback
from functools import wraps
import secrets

# Initialize Flask app and configurations
app = Flask(__name__)

# Ensure environment variables from .env are loaded BEFORE reading them
# This allows local development and Render env vars to work consistently
load_dotenv()

# --- Unified Config ---
database_url_env = os.environ.get('DATABASE_URL')
default_db_url = 'postgresql://menu_db_0gl8_user:6bd16fRcM0t9XKH7CpzpL8r6gIZcSTlM@dpg-d5oj6kk9c44c738nd2eg-a.oregon-postgres.render.com/menu_db_0gl8?sslmode=require'
if database_url_env:
    try:
        from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
        parsed = urlparse(database_url_env)
        query = dict(parse_qsl(parsed.query))
        if query.get('sslmode') is None:
            query['sslmode'] = 'require'  # Render requires SSL
        normalized = parsed._replace(query=urlencode(query))
        app.config['SQLALCHEMY_DATABASE_URI'] = urlunparse(normalized)
    except Exception:
        # Fallback to original env var if parsing fails
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url_env
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = default_db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    # Recycle connections proactively before provider idle timeouts
    'pool_recycle': 300,
    'pool_timeout': 30,
    'max_overflow': 20,
    'pool_size': 10,
    'pool_use_lifo': True,
    'pool_reset_on_return': 'rollback',
    # Add TCP keepalive parameters to reduce idle SSL disconnects
    'connect_args': {
        "sslmode": "require",  # Render requires SSL
        # Enable TCP keepalives at the PostgreSQL driver level
        "keepalives": 1,
        # Seconds of inactivity before sending keepalives (5 minutes)
        "keepalives_idle": 300,
        # Seconds between keepalive probes
        "keepalives_interval": 30,
        # Number of failed probes before dropping
        "keepalives_count": 5,
        # Avoid long hangs on first connection - increased for SSL handshake
        "connect_timeout": 20,
    }
}
app.config['SQLALCHEMY_POOL_SIZE'] = 10
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 20
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30
app.config['SQLALCHEMY_POOL_RECYCLE'] = 300
app.config['SQLALCHEMY_POOL_PRE_PING'] = True

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = None
app.config['WTF_CSRF_SECRET_KEY'] = os.environ.get('WTF_CSRF_SECRET_KEY', 'your-secret-key-here')

app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.example.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', '')

app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['CLOUDINARY_CLOUD_NAME'] = os.environ.get('CLOUDINARY_CLOUD_NAME')
app.config['CLOUDINARY_API_KEY'] = os.environ.get('CLOUDINARY_API_KEY')
app.config['CLOUDINARY_API_SECRET'] = os.environ.get('CLOUDINARY_API_SECRET')

# --- Extension Initialization ---
from extensions import db
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer

db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize CSRF protection with custom validation that skips API routes
class CustomCSRFProtect(CSRFProtect):
    def _exempt_from_csrf(self, view):
        """Override to check if view is an API route"""
        if hasattr(view, '__name__') and hasattr(view, '__module__'):
            # Check if the view is from the api module
            if 'api.' in view.__module__:
                return True
        return super()._exempt_from_csrf(view) if hasattr(super(), '_exempt_from_csrf') else False
    
    def protect(self):
        """Override protect method to skip CSRF for API routes"""
        # Skip CSRF protection for API routes
        if request.path.startswith('/api/'):
            return
        # Call the parent protect method for all other routes
        return super().protect()

csrf = CustomCSRFProtect(app)

# Alternative: Simple approach - exempt API blueprint after registration
mail = Mail(app)

# Register API Blueprint with CORS
from api import api_bp
from flask_cors import CORS

# Enable CORS for API routes
CORS(app, resources={
    r"/api/*": {
        "origins": os.environ.get('CORS_ORIGINS', '*').split(','),
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Register API blueprint  
app.register_blueprint(api_bp)

# Validate mail configuration at startup to surface issues early
try:
    if app.config.get('MAIL_SERVER') in (None, '', 'smtp.example.com'):
        logger.warning('MAIL_SERVER is not configured or still set to smtp.example.com')
    if not app.config.get('MAIL_DEFAULT_SENDER'):
        logger.warning('MAIL_DEFAULT_SENDER is not configured')
    if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
        logger.warning('MAIL_USERNAME or MAIL_PASSWORD not configured')
except Exception as _mail_cfg_err:
    logger.warning(f"Mail configuration check failed: {_mail_cfg_err}")

# --- Email Utilities ---
EMAIL_PROVIDER = os.environ.get('EMAIL_PROVIDER', 'smtp').lower()
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')

# If a SendGrid API key is present, prefer sendgrid automatically
try:
    if EMAIL_PROVIDER != 'sendgrid' and SENDGRID_API_KEY:
        EMAIL_PROVIDER = 'sendgrid'
        logger.info('EMAIL_PROVIDER auto-set to sendgrid based on SENDGRID_API_KEY presence')
    logger.info(f"Email provider: {EMAIL_PROVIDER}")
except Exception as _prov_err:
    logger.warning(f"Email provider detection/logging failed: {_prov_err}")

def _send_via_sendgrid(subject: str, recipients: list, text_body: Optional[str], html_body: Optional[str], sender: Optional[str]) -> None:
    if not SENDGRID_API_KEY:
        raise RuntimeError('SENDGRID_API_KEY not set')
    if not sender:
        sender = app.config.get('MAIL_DEFAULT_SENDER')
    if not sender:
        raise RuntimeError('MAIL_DEFAULT_SENDER not set')
    import requests
    payload = {
        "personalizations": [{"to": [{"email": r} for r in recipients]}],
        "from": {"email": sender},
        "subject": subject,
        "content": []
    }
    if text_body:
        payload["content"].append({"type": "text/plain", "value": text_body})
    if html_body:
        payload["content"].append({"type": "text/html", "value": html_body})
    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }
    resp = requests.post("https://api.sendgrid.com/v3/mail/send", json=payload, headers=headers, timeout=15)
    if resp.status_code not in (200, 202):
        raise RuntimeError(f"SendGrid error {resp.status_code}: {resp.text}")
def _send_email_sync(message: Message) -> None:
    try:
        if EMAIL_PROVIDER == 'sendgrid':
            _send_via_sendgrid(
                subject=message.subject,
                recipients=message.recipients,
                text_body=getattr(message, 'body', None),
                html_body=getattr(message, 'html', None),
                sender=getattr(message, 'sender', None)
            )
        else:
            mail.send(message)
        logger.info(f"Email sent to {message.recipients} via {EMAIL_PROVIDER}")
    except Exception as e:
        # Log full exception so deploy logs show the SMTP/connect error
        logger.exception(f"Failed to send email to {message.recipients}: {e}")

def send_email_async(message: Message) -> None:
    """Fire-and-forget email sender that logs any exceptions in thread."""
    def _runner(m: Message) -> None:
        _send_email_sync(m)
    threading.Thread(target=_runner, args=(message,), daemon=True).start()

# Optional: token-protected debug endpoint to verify outbound email from environment
EMAIL_DEBUG_TOKEN = os.environ.get('EMAIL_DEBUG_TOKEN')
@app.get('/__debug/email')
def debug_email_send():
    token = request.args.get('token')
    recipient = request.args.get('to')
    if not EMAIL_DEBUG_TOKEN or token != EMAIL_DEBUG_TOKEN:
        return ("Not found", 404)
    if not recipient:
        return ("Missing 'to'", 400)
    test_msg = Message(
        subject="BlueSpace Email Debug",
        recipients=[recipient],
        body="This is a BlueSpace Restaurants email debug test.")
    try:
        _send_email_sync(test_msg)
        return jsonify({"status": "sent", "to": recipient})
    except Exception as e:
        # Although _send_email_sync logs, also return error text for debugging
        return jsonify({"status": "error", "error": str(e)}), 500
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# --- Hardware Notifier Singleton ---
# Using the global SIMULATION_MODE and singleton accessor defined earlier
# Remove any direct HardwareNotifier() instantiation

def admin_panel_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        # If password not set, redirect to set password
        if not getattr(current_user, 'admin_panel_password_hash', None):
            return redirect(url_for('set_admin_panel_password'))
        # If not authenticated for admin panel, redirect to enter password
        if not session.get('admin_panel_authenticated'):
            return redirect(url_for('admin_panel_password'))
        return view_func(*args, **kwargs)
    return wrapped


        
# Attach the Flask teardown handler to remove session after each request
@app.teardown_appcontext
def shutdown_session(exception=None):
    """Clean up database session and hardware notifier on application shutdown"""
    try:
        db.session.remove()
    except Exception as e:
        app.logger.warning(f"Error removing database session: {str(e)}")
    
    # Cleanup hardware notifier
    try:
        cleanup_hardware_notifier()
    except Exception as e:
        app.logger.warning(f"Error cleaning up hardware notifier: {str(e)}")

# Add Flask shutdown handler
@app.teardown_appcontext
def cleanup_on_app_shutdown(exception=None):
    """Clean up resources when Flask app shuts down"""
    if shutdown_requested:
        cleanup_on_shutdown()

# --- End SQLAlchemy Engine/Session Setup ---


# (dotenv already loaded near app initialization)

# Initialize hardware notifier via singleton (already initialized above)

# Session configuration
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.config['SESSION_COOKIE_SECURE'] = True  # Only send cookie over HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Protect against CSRF

# Add template error handling
@app.errorhandler(500)
def handle_template_error(e):
    logger.error(f'Template error: {str(e)}')
    logger.error(f'Traceback: {traceback.format_exc()}')
    
    # Try to render a basic error page
    try:
        return render_template('error.html', error=str(e)), 500
    except:
        # If template rendering fails, fall back to a simple response
        return 'An error occurred while processing your request.', 500

from jinja2.exceptions import TemplateNotFound
@app.errorhandler(TemplateNotFound)
def handle_template_not_found(e):
    logger.error(f'Template not found: {str(e)}')
    return 'Template not found', 404

# Configure Cloudinary
cloudinary.config(
    cloud_name=app.config['CLOUDINARY_CLOUD_NAME'],
    api_key=app.config['CLOUDINARY_API_KEY'],
    api_secret=app.config['CLOUDINARY_API_SECRET']
)

# Add custom template filters
@app.template_filter('from_json')
def from_json(value):
    try:
        return json.loads(value)
    except:
        return []

@app.template_filter('format_price')
def format_price_filter(price, currency='USD'):
    currency_symbols = {
        'USD': '$',
        'KES': 'KSh',
        'EUR': '€',
        'GBP': '£',
        'INR': '₹',
        'AUD': 'A$',
        'CAD': 'C$',
        'JPY': '¥'
    }
    symbol = currency_symbols.get(currency, '$')
    return f"{symbol}{price:.2f}"

@app.template_filter('strftime')
def strftime_filter(date, format_string):
    """Custom filter to format dates using strftime"""
    if date is None:
        return ''
    try:
        return date.strftime(format_string)
    except:
        return str(date)

# Add API route for hardware notifications
@app.route('/api/orders', methods=['GET'])
def get_new_orders():
    restaurant_id = request.args.get("restaurant_id")
    status = request.args.get("status", "new")

    if not restaurant_id:
        return jsonify({"error": "restaurant_id is required"}), 400

    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            # Query orders matching restaurant ID and status (supports CSV of statuses)
            status_values = [s.strip() for s in status.split(',')] if ',' in status else [status]
            query = db.select(Order).where(Order.restaurant_id == int(restaurant_id))
            if status_values:
                if len(status_values) == 1:
                    query = query.where(Order.status == status_values[0])
                else:
                    query = query.where(Order.status.in_(status_values))
            orders = db.session.execute(query).scalars().all()

            # Return list of orders with expanded info for hardware display
            result = []
            for order in orders:
                try:
                    try:
                        parsed_items = json.loads(order.items) if order.items else []
                    except Exception:
                        parsed_items = []
                    result.append({
                        "id": order.id,
                        "order_type": order.order_type,
                        "status": order.status,
                        "created_at": order.created_at.isoformat() if getattr(order, 'created_at', None) else None,
                        "items": parsed_items,
                        "total_amount": float(order.total_amount) if getattr(order, 'total_amount', None) is not None else 0,
                        "customer_name": getattr(order, 'customer_name', '') or '',
                        "customer_phone": getattr(order, 'customer_phone', '') or '',
                        "delivery_address": getattr(order, 'delivery_address', '') or '',
                        "special_instructions": getattr(order, 'special_instructions', '') or ''
                    })
                except Exception:
                    result.append({
                    "id": order.id,
                    "order_type": order.order_type,
                    "status": order.status
                    })
            return jsonify(result)
            
        except sqlalchemy.exc.OperationalError as e:
            if attempt < max_retries - 1:
                app.logger.warning(f"Database connection error on attempt {attempt + 1}, retrying in {retry_delay}s: {str(e)}")
                gevent_sleep(retry_delay)
            else:
                app.logger.error(f"Database connection failed after {max_retries} attempts: {str(e)}")
                return jsonify({"error": str(e)}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500



# Password reset request route
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password_request():
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        from models import User
        user = db.session.execute(db.select(User).filter_by(email=form.email.data)).scalar_one_or_none()
        if user:
            # Generate token
            token = serializer.dumps(user.email, salt='password-reset-salt')
            reset_url = url_for('reset_password_token', token=token, _external=True)
            # Send email (HTML + text)
            subject = "Password Reset Request"
            from datetime import datetime as _dt
            html_body = render_template('emails/password_reset.html', reset_url=reset_url, current_year=_dt.utcnow().year)
            text_body = f"To reset your password, open this link:\n{reset_url}\nThis link will expire in 30 minutes."
            msg = Message(subject=subject, recipients=[user.email], body=text_body, html=html_body)
            mail.send(msg)
        flash('If your email is registered, you will receive a password reset link shortly.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', form=form)

# Password reset form route
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password_token(token):
    form = PasswordResetForm()
    from models import User
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=1800)  # 30 minutes
    except SignatureExpired:
        flash('The password reset link has expired.', 'danger')
        return redirect(url_for('reset_password_request'))
    except BadSignature:
        flash('Invalid or tampered reset link.', 'danger')
        return redirect(url_for('reset_password_request'))

    user = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
    if not user:
        flash('Invalid user.', 'danger')
        return redirect(url_for('reset_password_request'))

    if form.validate_on_submit():
        from werkzeug.security import generate_password_hash
        user.password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        from extensions import db
        db.session.commit()
        flash('Your password has been reset. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

# Add request logging  
@app.before_request
def log_csrf_token():
    # Health check for DB connection before every request
    try:
        db.session.execute(text('SELECT 1'))
    except Exception as e:
        db.session.rollback()
        app.logger.warning(f"DB connection dropped: {e}")
    if request.method == 'POST':
        # No-op placeholder to satisfy indentation; CSRF handled by Flask-WTF
        pass

# Make csrf_token() available in all templates
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)

# --- Restore auto_transition_order_status utility ---
def auto_transition_order_status(order_id):
    import threading
    import time
    from sqlalchemy.orm import scoped_session, sessionmaker
    from sqlalchemy import update
    
    # Use global auto_transition_timers
    global auto_transition_timers, shutdown_requested
    
    def transition_status():
        # Check if shutdown was requested
        if shutdown_requested:
            print(f"[auto_transition] Shutdown requested, skipping transition for order {order_id}")
            return
            
        try:
            print(f"[auto_transition] Timer started for order {order_id}")
            from app import app, db, Order
            with app.app_context():
                Session = scoped_session(sessionmaker(bind=db.engine))
                session = Session()
                try:
                    # Check if order still exists and is in 'new' status
                    order = session.get(Order, order_id)
                    if not order:
                        print(f"[auto_transition] Order {order_id} not found, skipping transition")
                        return
                    
                    # Only transition if still in 'new' status (not manually updated)
                    if order.status == 'new':
                        result = session.execute(
                            update(Order)
                            .where(Order.id == order_id, Order.status == 'new')
                            .values(status='pending')
                        )
                        if result.rowcount:
                            print(f"[ORDER STATUS] Order {order_id} status automatically transitioned to 'pending' at {datetime.now()}")
                            session.commit()
                            print(f"[auto_transition] Order {order_id} status automatically transitioned to 'pending'")
                        else:
                            print(f"[auto_transition] Order {order_id} status not changed (concurrent update or already changed)")
                    else:
                        print(f"[auto_transition] Order {order_id} status is '{order.status}', skipping auto-transition")
                finally:
                    session.close()
        except Exception as e:
            print(f"[auto_transition] Error in status transition for order {order_id}: {str(e)}")
        finally:
            # Clean up timer reference
            if order_id in auto_transition_timers:
                del auto_transition_timers[order_id]
    
    # Cancel existing timer if any
    if order_id in auto_transition_timers:
        auto_transition_timers[order_id].cancel()
        print(f"[auto_transition] Cancelled existing timer for order {order_id}")
    
    timer = threading.Timer(10.0, transition_status)
    auto_transition_timers[order_id] = timer
    timer.start()
    print(f"[auto_transition] Started auto-transition timer for order {order_id}")

# Load user
@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except Exception as e:
        db.session.rollback()
        app.logger.warning(f"Failed to load user {user_id}: {str(e)}")
        return None

# Register routes
@app.route('/')
def home():
    return render_template('home.html', restaurant_name="BlueSpace Restaurant")

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        confirm_password = form.confirm_password.data
        restaurant_name = form.restaurant_name.data
        currency = form.currency.data
        logo = form.logo.data

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html', form=form)

        if db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none():
            flash('Email already exists.', 'danger')
            return render_template('register.html', form=form)

        logo_url = None
        if logo and getattr(logo, 'filename', None):
            try:
                upload_result = cloudinary.uploader.upload(logo, folder=f"logos/{email.replace('@', '_')}")
                logo_url = upload_result.get('secure_url')
            except Exception as e:
                flash(f'Logo upload failed: {str(e)}', 'danger')
                return render_template('register.html', form=form)

        # Generate and send verification code; store pending registration in session
        import random
        verification_code = f"{random.randint(100000, 999999)}"
        session['pending_registration'] = {
            'email': email,
            'password': generate_password_hash(password, method='pbkdf2:sha256'),
            'restaurant_name': restaurant_name,
            'currency': currency,
            'logo_url': logo_url,
            'code': verification_code,
            'created_at': datetime.utcnow().isoformat()
        }

        try:
            from datetime import datetime as _dt
            html_body = render_template('emails/verify_code.html', code=verification_code, current_year=_dt.utcnow().year)
            text_body = f"Your BlueSpace Restaurants verification code is: {verification_code}\nThis code expires in 30 minutes."
            msg = Message(subject="Verify your email",
                          recipients=[email],
                          body=text_body,
                          html=html_body)
            # Send asynchronously with logging
            send_email_async(msg)
        except Exception as e:
            session.pop('pending_registration', None)
            flash(f'Failed to send verification email: {str(e)}', 'danger')
            return render_template('register.html', form=form)

        session.modified = True
        return redirect(url_for('verify_registration'))

    return render_template('register.html', form=form)

@app.route('/verify-registration', methods=['GET', 'POST'])
def verify_registration():
    pending = session.get('pending_registration')
    if not pending:
        flash('No registration pending. Please register again.', 'warning')
        return redirect(url_for('register'))

    form = RegistrationVerificationForm()
    if request.method == 'POST' and form.validate_on_submit():
        code_entered = form.verification_code.data.strip()
        if code_entered != pending.get('code'):
            flash('Invalid verification code.', 'danger')
            return render_template('verify_registration.html', form=form, email=pending.get('email'))

        # Create user after successful verification
        try:
            new_user = User(
                email=pending['email'],
                password=pending['password'],
                restaurant_name=pending['restaurant_name'],
                logo_url=pending['logo_url'],
                currency=pending['currency']
            )
            db.session.add(new_user)
            db.session.commit()

            # Generate QR
            qr_data = url_for('restaurant_menu', user_id=new_user.id, _external=True)
            qr = qrcode.QRCode(version=1, error_correction=ERROR_CORRECT_H, box_size=10, border=4)
            qr.add_data(qr_data)
            qr.make(fit=True)
            qr_image = qr.make_image(fill_color="#e67e22", back_color="white")

            if new_user.logo_url:
                try:
                    response = requests.get(new_user.logo_url, stream=True)
                    response.raise_for_status()
                    logo_image = Image.open(response.raw)
                    qr_size = qr_image.size[0]
                    logo_size = int(qr_size * 0.3)
                    logo_image.thumbnail((logo_size, logo_size))
                    pos = ((qr_size - logo_image.size[0]) // 2, (qr_size - logo_image.size[1]) // 2)
                    logo_bg = Image.new('RGBA', logo_image.size, 'white')
                    logo_bg.paste(logo_image, (0, 0))
                    qr_image.paste(logo_bg, pos)
                except Exception as e:
                    logger.warning(f"Error adding logo to QR code: {str(e)}")

            qr_buffer = io.BytesIO()
            qr_image.save(qr_buffer, format='PNG')
            qr_buffer.seek(0)

            try:
                qr_upload_result = cloudinary.uploader.upload(qr_buffer, folder=f"qr_codes/{new_user.email.replace('@', '_')}")
                new_user.qr_url = qr_upload_result.get('secure_url')
                db.session.commit()
            except Exception as e:
                logger.warning(f"Error uploading QR code: {str(e)}")
                flash('Account created, but failed to generate QR code.', 'warning')

            flash('Email verified and account created! Please login.', 'success')
            session.pop('pending_registration', None)
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            logger.exception("Registration verification failed")
            flash(f'Failed to complete registration: {str(e)}', 'danger')
            return render_template('verify_registration.html', form=form, email=pending.get('email'))

    return render_template('verify_registration.html', form=form, email=pending.get('email'))

@app.route('/verify-registration/resend', methods=['POST'])
def resend_verification_code():
    pending = session.get('pending_registration')
    if not pending:
        flash('No registration pending. Please register again.', 'warning')
        return redirect(url_for('register'))

    import random
    new_code = f"{random.randint(100000, 999999)}"
    pending['code'] = new_code
    session['pending_registration'] = pending
    session.modified = True

    try:
        from datetime import datetime as _dt
        html_body = render_template('emails/verify_code.html', code=new_code, current_year=_dt.utcnow().year)
        text_body = f"Your BlueSpace Restaurants verification code is: {new_code}\nThis code expires in 30 minutes."
        msg = Message(subject="Verify your email",
                      recipients=[pending['email']],
                      body=text_body,
                      html=html_body)
        send_email_async(msg)
        flash('A new verification code has been sent.', 'info')
    except Exception as e:
        flash(f'Failed to resend verification email: {str(e)}', 'danger')

    return redirect(url_for('verify_registration'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    next_page = request.args.get('next')
    if current_user.is_authenticated:
        app.logger.debug(f'User already authenticated: {current_user.get_id()}')
        return redirect(next_page or url_for('dashboard'))
        
    # Handle form data
    form = LoginForm()
    if request.method == 'POST':
        if not form.validate_on_submit():
            return render_template('login.html', form=form, next=next_page)
            
        email = form.email.data
        password = form.password.data
        remember = form.remember.data

        app.logger.debug(f"Login attempt for email: {email}")
        app.logger.debug(f"Session before login: {dict(session)}")
        
        user = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
        if user:
            app.logger.debug(f"User found: {user.restaurant_name} (ID: {user.id})")
            if check_password_hash(user.password, password):
                app.logger.debug("Password verified, logging in user")
                app.logger.debug(f"User ID: {user.id}, User email: {user.email}")
                
                login_user(user, remember=remember)
                
                # Update user's last login time
                user.last_login = datetime.now(UTC)
                db.session.commit()
                
                app.logger.debug(f"Session after login: {dict(session)}")
                app.logger.debug(f"Current user after login: {current_user.get_id() if current_user.is_authenticated else 'None'}")
                

                next_page = request.args.get('next')
                if not next_page or not next_page.startswith('/'):
                    next_page = url_for('dashboard')
                app.logger.debug(f"Redirecting to: {next_page}")
                return redirect(next_page)
            else:
                app.logger.debug("Invalid password")
                flash('Invalid password', 'danger')
                return render_template('login.html', form=form, next=next_page)
        else:
            app.logger.debug("User not found")
            flash('User not found', 'danger')
            return render_template('login.html', form=form, next=next_page)
    return render_template('login.html', form=form, next=next_page)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('admin_panel_authenticated', None)
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        app.logger.debug(f"Dashboard access attempt for user: {current_user.get_id()}")
        app.logger.debug(f"Session contents: {dict(session)}")
        
        # Get menu items
        menu_items = db.session.execute(db.select(MenuItem).where(MenuItem.user_id == current_user.id)).scalars().all()
        current_menu_item_count = len(menu_items)
        # Get pending orders count (exclude archived)
        pending_statuses = ['new', 'pending', 'paid', 'preparing', 'ready']
        pending_dine_in = db.session.execute(db.select(func.count()).select_from(Order).where(
            Order.restaurant_id == current_user.id,
            Order.status.in_(pending_statuses),
            Order.order_type == 'dine_in',
            Order.status != 'archived'
        )).scalar() or 0
        pending_delivery = db.session.execute(db.select(func.count()).select_from(Order).where(
            Order.restaurant_id == current_user.id,
            Order.status.in_(pending_statuses),
            Order.order_type == 'delivery',
            Order.status != 'archived'
        )).scalar() or 0
        # Calculate today's revenue from delivered orders (exclude archived)
        today = datetime.now(UTC).date()
        start = datetime.combine(today, datetime_time.min)
        end = datetime.combine(today, datetime_time.max)
        today_delivered_orders = db.session.execute(db.select(Order).where(
            Order.restaurant_id == current_user.id,
            Order.status == 'delivered',
            Order.created_at.between(start, end)
        )).scalars().all()
        today_revenue = sum(order.total_amount for order in today_delivered_orders)
        # Only count non-archived orders
        total_orders = db.session.execute(db.select(func.count()).select_from(Order).where(
            Order.restaurant_id == current_user.id,
            Order.status != 'archived'
        )).scalar() or 0
        return render_template('dashboard.html',
                             menu_items=menu_items,
                             pending_dine_in=pending_dine_in,
                             pending_delivery=pending_delivery,
                             today_revenue=today_revenue,
                             total_orders=total_orders,
                             delete_form=DeleteForm(),
                             currency=current_user.currency,
                             csrf_token=generate_csrf(),
                             current_menu_item_count=current_menu_item_count,
                             menu_item_limit=None)
    except Exception as e:
        logger.error(f"Error in dashboard route: {str(e)}")
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        return redirect(url_for('home'))

@app.route('/add_menu_item', methods=['GET', 'POST'])
@login_required
def add_menu_item():

    form = MenuItemForm()
    categories = db.session.execute(db.select(Category)).scalars().all()
    form.category_id.choices = [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        # Handle image upload or URL
        image_url = form.image_url.data
        
        # Check if a file was uploaded
        if form.item_image.data and form.item_image.data.filename:
            try:
                # Upload to Cloudinary
                upload_result = cloudinary.uploader.upload(
                    form.item_image.data, 
                    folder=f"menu_items/{current_user.id}"
                )
                image_url = upload_result['secure_url']
                flash('Image uploaded successfully!', 'success')
            except Exception as e:
                app.logger.error(f"Failed to upload image: {str(e)}")
                flash('Failed to upload image. Please try again or use an image URL.', 'warning')
                current_menu_item_count = db.session.execute(db.select(MenuItem).where(MenuItem.user_id == current_user.id)).scalar()
                return render_template('add_menu_item.html', form=form, currency=currency, currency_symbol=currency_symbol, current_menu_item_count=current_menu_item_count, menu_item_limit=None)
        
        menu_item = MenuItem(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            image_url=image_url,
            stock=form.stock.data,
            user_id=current_user.id,
            category_id=form.category_id.data
        )
        db.session.add(menu_item)
        db.session.commit()
        flash('Menu item added!', 'success')
        return redirect(url_for('dashboard'))
    currency = current_user.currency
    currency_symbol = get_currency_symbol(currency)
    current_menu_item_count = db.session.execute(db.select(MenuItem).where(MenuItem.user_id == current_user.id)).scalar()
    return render_template('add_menu_item.html', form=form, currency=currency, currency_symbol=currency_symbol, current_menu_item_count=current_menu_item_count, menu_item_limit=None)

@app.route('/edit_menu_item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_menu_item(item_id):
    item = db.session.get(MenuItem, item_id)
    if not item:
        abort(404)
    form = MenuItemForm(obj=item)
    categories = db.session.execute(db.select(Category)).scalars().all()
    form.category_id.choices = [(c.id, c.name) for c in categories]
    if request.method == 'GET':
        form.category_id.data = item.category_id
    if form.validate_on_submit():
        print("Submitted category_id:", form.category_id.data)
        
        # Handle image upload or URL
        image_url = form.image_url.data
        
        # Check if a file was uploaded
        if form.item_image.data and form.item_image.data.filename:
            try:
                # Upload to Cloudinary
                upload_result = cloudinary.uploader.upload(
                    form.item_image.data, 
                    folder=f"menu_items/{current_user.id}"
                )
                image_url = upload_result['secure_url']
                flash('Image uploaded successfully!', 'success')
            except Exception as e:
                app.logger.error(f"Failed to upload image: {str(e)}")
                flash('Failed to upload image. Please try again or use an image URL.', 'warning')
                return render_template('edit_menu_item.html', form=form, item=item, categories=categories)
        
        item.name = form.name.data
        item.description = form.description.data
        item.price = form.price.data
        item.image_url = image_url
        item.stock = form.stock.data
        item.category_id = form.category_id.data
        db.session.commit()
        print("Saved item.category_id in DB:", item.category_id)
        flash('Menu item updated!', 'success')
        return redirect(url_for('dashboard'))
    # Always return a response
    return render_template('edit_menu_item.html', form=form, item=item, categories=categories)

@app.route('/restaurant/<int:user_id>', methods=['GET', 'POST'])
def restaurant_menu(user_id):
    print(f"Attempting to access restaurant menu for user_id: {user_id}")
    max_retries = 3
    retry_delay = 1  # seconds
    for attempt in range(max_retries):
        try:
            user = db.session.get(User, user_id)
            if not user:
                return jsonify({"success": False, "message": "Restaurant not found."}), 404
            print(f"Found user: {user.restaurant_name}")
            categories = db.session.execute(db.select(Category)).scalars().all()
            all_items = db.session.execute(db.select(MenuItem).filter_by(user_id=user_id)).scalars().all()
            print("All menu items for user_id", user_id)
            for mi in all_items:
                print(f"Item: {mi.id}, Name: {mi.name}, Category ID: {mi.category_id}")
            selected_category_id = request.args.get('category', type=int)
            print("Selected category_id from request:", selected_category_id)
            if selected_category_id:
                menu_items = db.session.execute(db.select(MenuItem).filter_by(user_id=user_id, category_id=selected_category_id)).scalars().all()
            else:
                menu_items = db.session.execute(db.select(MenuItem).filter_by(user_id=user_id)).scalars().all()
            print(f"Found {len(menu_items)} menu items")

            # --- Handle AJAX/JSON POST for order creation ---
            if request.method == 'POST':
                if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Accept') == 'application/json':
                    try:
                        data = request.get_json(force=True)
                        items = data.get('items', [])
                        table_number = data.get('table_number')
                        special_instructions = data.get('special_instructions', '')
                        order_type = data.get('order_type', 'dine_in')
                        customer_name = data.get('customer_name', '')
                        customer_phone = data.get('customer_phone', '')
                        delivery_address = data.get('delivery_address', '')
                        total = data.get('total_amount', 0)

                        # --- BLOCK direct order creation if payment method is stk_push ---
                        if user.payment_method == 'stk_push':
                            return jsonify({'success': False, 'message': 'Order cannot be placed directly. Please use STK Push payment.'}), 400

                        if not items or total <= 0:
                            return jsonify({'success': False, 'message': 'No items or invalid total.'}), 400
                        
                        # --- ENHANCED DUPLICATE ORDER PREVENTION ---
                        from enhanced_duplicate_prevention import enhanced_duplicate_check, clear_session_duplicate
                        
                        # Use enhanced duplicate checking with multiple layers
                        duplicate_check = enhanced_duplicate_check(data, user_id)
                        if duplicate_check['is_duplicate']:
                            return jsonify({
                                'success': False, 
                                'message': duplicate_check['message'],
                                'duplicate_order_id': duplicate_check.get('duplicate_order_id'),
                                'reason': duplicate_check.get('reason', 'unknown')
                            }), 409

                        # Create new order
                        new_order = Order(
                            table_number=table_number,
                            items=json.dumps(items),
                            special_instructions=special_instructions,
                            user_id=user_id,
                            restaurant_id=user_id,  # Explicitly set restaurant_id
                            total_amount=total,
                            order_type=order_type,
                            customer_name=customer_name,
                            customer_phone=customer_phone,
                            delivery_address=delivery_address
                        )
                        
                        # Set initial status based on payment method
                        if user.payment_method == 'manual':
                            new_order.status = 'pending_confirmation'
                        else:
                            new_order.status = 'new'
                        
                        db.session.add(new_order)
                        db.session.commit()
                        print(f"Order created: {new_order.id}")
                        print(f"Order restaurant_id: {new_order.restaurant_id}")
                        print(f"Order user_id: {new_order.user_id}")
                        print(f"Order status: {new_order.status}")
                        
                        # Notify hardware about new order
                        try:
                            notify_hardware({'status': 'new'})
                        except Exception as e:
                            print(f"Error notifying hardware: {str(e)}")
                        
                        # Start auto-transition to 'pending' after 10 seconds only for non-manual payment orders
                        if user.payment_method != 'manual':
                            try:
                                auto_transition_order_status(new_order.id)
                            except Exception as e:
                                print(f"Error starting auto-transition: {str(e)}")
                        else:
                            print(f"Manual payment order {new_order.id} - skipping auto-transition")
                        
                        # Prepare manual payment details for frontend
                        manual_payment_details = None
                        if user.payment_method == 'manual':
                            if getattr(user, 'mpesa_receiving_method', None) == 'paybill' and getattr(user, 'mpesa_paybill', None):
                                manual_payment_details = {'type': 'paybill', 'number': user.mpesa_paybill}
                            elif getattr(user, 'mpesa_receiving_method', None) == 'till' and getattr(user, 'mpesa_till', None):
                                manual_payment_details = {'type': 'till', 'number': user.mpesa_till}
                            elif getattr(user, 'mpesa_receiving_method', None) == 'phone' and getattr(user, 'mpesa_phone_receiver', None):
                                manual_payment_details = {'type': 'phone', 'number': user.mpesa_phone_receiver}
                        # Clear session duplicate hash after successful order
                        if 'order_hash' in duplicate_check:
                            clear_session_duplicate(duplicate_check['order_hash'])
                        return jsonify({'success': True, 'order_id': new_order.id, 'message': 'Order placed successfully.', 'total': new_order.total_amount, 'payment_method': user.payment_method, 'manual_payment_details': manual_payment_details})
                    except Exception as e:
                        db.session.rollback()
                        print(f"Order creation error: {str(e)}")
                        return jsonify({'success': False, 'message': str(e)}), 500
                else:
                    # Fallback for normal POSTs (form submission)
                    flash('Order placement via form is not supported. Please use the menu page.', 'danger')
                    return redirect(url_for('restaurant_menu', user_id=user_id))

            # --- Normal GET: Render menu page ---
            return render_template('restaurant_menu.html', user=user, menu_items=menu_items, categories=categories, selected_category_id=selected_category_id, csrf_token=generate_csrf())
        except Exception as e:
            app.logger.error(f"Error in restaurant_menu: {str(e)}")
            # Avoid rendering template with user=None to prevent Jinja errors
            return abort(500)
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    
    # Get the latest order for this user
    latest_order = db.session.execute(db.select(Order).filter_by(user_id=user_id).order_by(Order.created_at.desc())).scalar_one_or_none()
    
    if not latest_order:
        flash('No order found.', 'warning')
        return redirect(url_for('restaurant_menu', user_id=user_id))
    
    return render_template('order_success.html', 
                         user=user,
                         order=latest_order)

@app.route('/orders')
@login_required
def view_orders():
    from sqlalchemy.orm import scoped_session, sessionmaker
    Session = scoped_session(sessionmaker(bind=db.engine))
    with Session() as session:
        session.expire_all()
        max_retries = 3
        retry_delay = 1  # seconds
        for attempt in range(max_retries):
            try:
                # Show active (non-archived) orders for management
                dine_in_orders = session.query(Order).filter(
                    Order.restaurant_id == current_user.id,
                    Order.order_type == 'dine_in',
                    (Order.is_archived.is_(False)) | (Order.is_archived.is_(None))
                ).order_by(Order.created_at.desc()).all()
                delivery_orders = session.query(Order).filter(
                    Order.restaurant_id == current_user.id,
                    Order.order_type == 'delivery',
                    (Order.is_archived.is_(False)) | (Order.is_archived.is_(None))
                ).order_by(Order.created_at.desc()).all()
                print(f"Orders view - Current user ID: {current_user.id}")
                print(f"Found {len(dine_in_orders)} dine-in orders and {len(delivery_orders)} delivery orders for restaurant {current_user.id}")
                all_orders = session.query(Order).filter(Order.restaurant_id == current_user.id).all()
                print(f"Total orders for restaurant {current_user.id}: {len(all_orders)}")
                for order in all_orders:
                    print(f"Order {order.id}: status={order.status}, type={order.order_type}, created={order.created_at}")
                return render_template('orders.html', 
                                     dine_in_orders=dine_in_orders,
                                     delivery_orders=delivery_orders,
                                     user_currency=current_user.currency,
                                     csrf_token=generate_csrf())
            except sqlalchemy.exc.OperationalError as e:
                app.logger.error(f"Database error loading orders: {str(e)}")
                flash('Database connection error. Please try again.', 'error')
                return render_template('orders.html', 
                                     dine_in_orders=[],
                                     delivery_orders=[],
                                     user_currency=current_user.currency,
                                     csrf_token=generate_csrf())
            except Exception as e:
                app.logger.error(f"Unexpected error loading orders: {str(e)}")
                flash('Error loading orders', 'error')
                return render_template('orders.html', 
                                     dine_in_orders=[],
                                     delivery_orders=[],
                                     user_currency=current_user.currency,
                                     csrf_token=generate_csrf())

@app.route('/orders/archive-delivered', methods=['POST'])
@login_required
def archive_delivered_orders():
    try:
        from sqlalchemy.orm import scoped_session, sessionmaker
        Session = scoped_session(sessionmaker(bind=db.engine))
        with Session() as session:
            delivered_orders = session.query(Order).filter(
                Order.restaurant_id == current_user.id,
                Order.status == 'delivered',
                (Order.is_archived.is_(False)) | (Order.is_archived.is_(None))
            ).all()

            archived_count = 0
            for order in delivered_orders:
                txns = session.query(CommissionTransaction).filter_by(order_id=order.id).all()
                if not txns or all(t.status == 'paid' for t in txns):
                    order.is_archived = True
                    order.archived_at = datetime.now(UTC)
                    archived_count += 1
            session.commit()
            flash(f'Archived {archived_count} delivered order(s).', 'success')
        return redirect(url_for('view_orders'))
    except Exception as e:
        app.logger.error(f"Error archiving delivered orders: {str(e)}")
        flash('Error archiving orders', 'error')
        return redirect(url_for('view_orders'))


@app.route('/delete_menu_item/<int:item_id>', methods=['POST'])
@login_required
def delete_menu_item(item_id):
    try:
        # Log request headers for debugging
        app.logger.debug(f"Request headers: {dict(request.headers)}")
        
        # Validate CSRF token for JSON requests
        if request.is_json:
            # Try both header names (case-insensitive)
            csrf_token = request.headers.get('X-CSRF-Token') or request.headers.get('X-Csrftoken')
            if not csrf_token:
                app.logger.warning(f"CSRF token missing in headers: {dict(request.headers)}")
                return jsonify({'success': False, 'error': 'CSRF token missing'}), 400
            try:
                validate_csrf(csrf_token)
                app.logger.debug(f"CSRF token validated successfully: {csrf_token[:10]}...")
            except Exception as e:
                app.logger.error(f"CSRF token validation failed: {str(e)}")
                return jsonify({'success': False, 'error': f'Invalid CSRF token: {str(e)}'}), 400

        # Bulk delete the menu item for the current user
        result = db.session.execute(db.delete(MenuItem).where(MenuItem.id == item_id, MenuItem.user_id == current_user.id))
        db.session.commit()
        if getattr(result, 'rowcount', None) is not None and result.rowcount == 0:
            app.logger.warning(f'Menu item not found: {item_id}')
            return jsonify({'success': False, 'error': 'Menu item not found'}), 404
        # SSE: Broadcast menu item deletion
        broadcast_menu_update(current_user.id, {
            'type': 'menu_delete',
            'item_id': item_id
        })
        return jsonify({'success': True, 'message': 'Menu item deleted successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting menu item: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.session.close()

@app.route('/api/order/<int:order_id>')
@login_required
def get_order_details(order_id):
    with Session() as session:
        order = session.get(Order, order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        # Ensure the current user owns this order
        if order.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        # Parse the items JSON string
        try:
            items = json.loads(order.items)
        except json.JSONDecodeError:
            items = []
        return jsonify({
            'id': order.id,
            'table_number': order.table_number,
            'items': items,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'total_amount': order.total_amount,
            'status': order.status
        })

@app.route('/api/order/<int:order_id>/deliver', methods=['POST'])
@login_required
def mark_order_delivered(order_id):
    try:
        # Validate CSRF token for JSON requests
        if request.is_json:
            # Validate CSRF token
            csrf_token = request.headers.get('X-CSRFToken')
            if not csrf_token:
                app.logger.error(f"CSRF token missing")
                return jsonify({'success': False, 'error': 'CSRF token missing'}), 400
            try:
                validate_csrf(csrf_token)
            except Exception as e:
                app.logger.error(f"CSRF token validation failed: {str(e)}")
                return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 400

            # Process order delivery
            order = db.session.get(Order, order_id)
            if not order:
                return jsonify({'success': False, 'error': 'Order not found'}), 404
            
            # Ensure the current user owns this order
            if order.user_id != current_user.id:
                return jsonify({'error': 'Unauthorized'}), 403
            
            order.status = 'delivered'
            print(f"[ORDER STATUS] Order {order.id} status changed to 'delivered' at {datetime.now()}")
            db.session.commit()

            # Decrement stock for each menu item in the order and broadcast update
            try:
                items = json.loads(order.items)
                for item in items:
                    menu_item = db.session.get(MenuItem, item.get('item_id'))
                    if menu_item and menu_item.user_id == current_user.id:
                        menu_item.stock = max(0, menu_item.stock - item['quantity'])
                        db.session.commit()
                        app.logger.info(f"Decremented stock for item_id={menu_item.id}: new stock={menu_item.stock}")
                        broadcast_menu_update(menu_item.user_id, {
                            'type': 'stock_update',
                            'item_id': menu_item.id,
                            'new_stock': menu_item.stock
                        })
                    else:
                        app.logger.error(f"MenuItem not found for item_id={item.get('item_id')} (user_id={current_user.id})")
            except Exception as e:
                app.logger.error(f"Error decrementing stock or broadcasting: {str(e)}")

            # Calculate updated revenue for today
            today = datetime.now().date()
            
            # Get all delivered orders
            delivered_orders = db.session.execute(db.select(Order).where(
                Order.user_id == current_user.id,
                Order.status == 'delivered'
            )).scalars().all()
            
            # Filter orders for today
            today_delivered_orders = [
                order for order in delivered_orders 
                if order.created_at.date() == today
            ]
            
            today_revenue = sum(order.total_amount for order in today_delivered_orders)
            
            return jsonify({
                'success': True,
                'today_revenue': format_price_filter(today_revenue, current_user.currency)
            })
    except Exception as e:
        app.logger.error(f"Error marking order as delivered: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/order/<int:order_id>', methods=['DELETE'])
@login_required
def delete_order(order_id):
    try:
        # Validate CSRF token for JSON requests
        if request.is_json:
            # Validate CSRF token
            csrf_token = request.headers.get('X-CSRFToken')
            if not csrf_token:
                app.logger.error(f"CSRF token missing")
                return jsonify({'success': False, 'error': 'CSRF token missing'}), 400
            try:
                validate_csrf(csrf_token)
            except Exception as e:
                app.logger.error(f"CSRF token validation failed: {str(e)}")
                return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 400

            # Process order deletion
            order = db.session.get(Order, order_id)
            if not order:
                return jsonify({'success': False, 'error': 'Order not found'}), 404
            
            # Ensure the current user owns this order
            if order.user_id != current_user.id:
                return jsonify({'error': 'Unauthorized'}), 403
            
            # Check if order is paid
            if order.status != 'paid':
                return jsonify({
                    'success': False,
                    'error': 'Only paid orders can be deleted'
                }), 400
            
            db.session.delete(order)
            db.session.commit()
            
            return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error in delete_order: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/dashboard-updates')
@login_required
def dashboard_updates():
    def generate():
        from sqlalchemy.orm import scoped_session, sessionmaker
        Session = scoped_session(sessionmaker(bind=db.engine))
        session = Session()
        session.expire_all()
        try:
            last_sent = None
            # Yield initial heartbeat to send headers
            yield ': heartbeat\n\n'
            print(f"Dashboard updates - Current user ID: {current_user.id}")
            while True:
                try:
                    pending_statuses = ['new', 'pending', 'paid', 'preparing', 'ready']
                    pending_dine_in = session.query(Order).filter(
                        Order.restaurant_id == current_user.id,
                        Order.status.in_(pending_statuses),
                        Order.order_type == 'dine_in',
                        Order.status != 'archived'
                    ).count()
                    pending_delivery = session.query(Order).filter(
                        Order.restaurant_id == current_user.id,
                        Order.status.in_(pending_statuses),
                        Order.order_type == 'delivery',
                        Order.status != 'archived'
                    ).count()
                    print(f"Dashboard updates - Pending dine-in: {pending_dine_in}, Pending delivery: {pending_delivery}")
                    all_orders = session.query(Order).filter(Order.restaurant_id == current_user.id).all()
                    print(f"Dashboard updates - Total orders for restaurant {current_user.id}: {len(all_orders)}")
                    for order in all_orders:
                        print(f"Dashboard updates - Order {order.id}: status={order.status}, type={order.order_type}, created={order.created_at}")
                    today = datetime.now().date()
                    delivered_orders = session.query(Order).filter(
                        Order.restaurant_id == current_user.id,
                        Order.status == 'delivered'
                    ).all()
                    today_delivered_orders = [
                        order for order in delivered_orders 
                        if order.created_at.date() == today
                    ]
                    today_revenue = sum(order.total_amount for order in today_delivered_orders)
                    total_orders = session.query(Order).filter(
                        Order.restaurant_id == current_user.id,
                        Order.status != 'archived'
                    ).count()
                    data = {
                        'pending_dine_in': pending_dine_in,
                        'pending_delivery': pending_delivery,
                        'delivered_orders': len(delivered_orders),
                        'today_revenue': format_price_filter(today_revenue, current_user.currency),
                        'total_orders': total_orders,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    if last_sent is None or json.dumps(data, sort_keys=True) != last_sent:
                        yield f"data: {json.dumps(data)}\n\n"
                        last_sent = json.dumps(data, sort_keys=True)
                except Exception as e:
                    print(f"Error in dashboard updates stream: {str(e)}")
                    yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                time_module.sleep(5)
        except GeneratorExit:
            print("Client disconnected from /dashboard-updates")
        finally:
            session.close()
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/order-updates')
@login_required
def order_updates():
    def generate():
        try:
            from sqlalchemy.orm import scoped_session, sessionmaker
            Session = scoped_session(sessionmaker(bind=db.engine))
            session = Session()
            
            # Track last sent orders to avoid duplicates with better structure
            last_sent_orders = {}  # {order_id: (status, updated_at)}
            last_check = datetime.now() - timedelta(minutes=5)
            last_status_check = datetime.now() - timedelta(minutes=5)
            
            while True:
                try:
                    updated_orders = session.query(Order).filter(
                        Order.restaurant_id == current_user.id,
                        Order.updated_at > last_status_check
                    ).order_by(Order.updated_at.asc()).all()
                    new_orders = session.query(Order).filter(
                        Order.restaurant_id == current_user.id,
                        Order.created_at > last_check
                    ).order_by(Order.created_at.asc()).all()
                    
                    # Filter out already sent orders with better logic
                    new_updated_orders = []
                    new_new_orders = []
                    
                    for order in updated_orders:
                        order_key = (order.id, order.status, order.updated_at)
                        if order.id not in last_sent_orders or last_sent_orders[order.id] != order_key:
                            new_updated_orders.append(order)
                            last_sent_orders[order.id] = order_key
                    
                    for order in new_orders:
                        order_key = (order.id, order.status, order.updated_at)
                        if order.id not in last_sent_orders or last_sent_orders[order.id] != order_key:
                            new_new_orders.append(order)
                            last_sent_orders[order.id] = order_key
                    
                    if new_updated_orders or new_new_orders:
                        print(f"Order updates - Found {len(new_updated_orders)} updated orders and {len(new_new_orders)} new orders")
                        for order in new_updated_orders + new_new_orders:
                            print(f"Order {order.id}: status={order.status}, type={order.order_type}, created={order.created_at}")
                    
                    if new_updated_orders or new_new_orders:
                        for order in new_updated_orders + new_new_orders:
                            try:
                                order_data = {
                                    'id': order.id,
                                    'table_number': order.table_number,
                                    'items': json.loads(order.items),
                                    'total_amount': float(order.total_amount),
                                    'created_at': order.created_at.isoformat(),
                                    'special_instructions': order.special_instructions,
                                    'status': order.status,
                                    'order_type': order.order_type,
                                    'customer_name': order.customer_name,
                                    'customer_phone': order.customer_phone,
                                    'delivery_address': order.delivery_address,
                                    'update_type': 'updated' if order in new_updated_orders else 'new',
                                    'is_delivery': order.order_type == 'delivery'
                                }
                                yield f"data: {json.dumps(order_data)}\n\n"
                            except json.JSONDecodeError:
                                continue
                        if new_new_orders:
                            last_check = new_new_orders[-1].created_at
                        if new_updated_orders:
                            last_status_check = new_updated_orders[-1].updated_at
                    
                    # Clean up old order IDs from tracking dict (keep only last 200)
                    if len(last_sent_orders) > 200:
                        # Keep only the most recent orders
                        sorted_orders = sorted(last_sent_orders.items(), key=lambda x: x[1][2], reverse=True)
                        last_sent_orders = dict(sorted_orders[:100])
                    
                    time_module.sleep(5)
                except Exception as e:
                    print(f"Error in order updates stream: {str(e)}")
                    yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                    time_module.sleep(5)
        except GeneratorExit:
            print("Client disconnected from /order-updates")
        finally:
            session.close()
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/clear_orders', methods=['POST'])
@login_required
def clear_orders():
    try:
        # Get all orders for the current user
        orders = db.session.execute(db.select(Order).filter_by(user_id=current_user.id)).scalars().all()
        if not orders:
            flash('No orders found to clear.', 'info')
            return redirect(url_for('view_orders'))
            
        # Delete all orders
        db.session.execute(db.delete(Order).where(Order.user_id == current_user.id))
        db.session.commit()
        flash(f'Successfully cleared {len(orders)} orders.', 'success')
        return redirect(url_for('view_orders'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error clearing orders: {str(e)}', 'danger')
        return redirect(url_for('view_orders'))
    return jsonify({'success': True})

@app.route('/analytics')
@login_required
@admin_panel_required
def analytics():
    # Remove role/session check so all logged-in users can access
    user_id = current_user.id
    now = datetime.now()

    # View selector: 'monthly', 'weekly', 'daily', 'hourly', 'range'
    view = request.args.get('view', 'monthly')
    daterange = request.args.get('daterange')

    grouped_orders = []

    if view == 'range' and daterange:
        try:
            start_str, end_str = daterange.split(' - ')
            start_date = datetime.strptime(start_str.strip(), '%Y-%m-%d')
            end_date = datetime.strptime(end_str.strip(), '%Y-%m-%d') + timedelta(days=1)

            grouped_orders = db.session.query(
                func.date(Order.created_at).label('label'),
                func.sum(Order.total_amount).label('revenue')
            ).filter(
                Order.user_id == user_id,
                Order.status == 'delivered',
                Order.created_at >= start_date,
                Order.created_at < end_date
            ).group_by('label').order_by('label').all()
        except Exception as e:
            print(f"Error parsing daterange: {e}")

    elif view == 'daily':
        # Calculate the start date for the last 7 days
        start_date = now.date() - timedelta(days=6)

        # Query for delivered orders in the last 7 days, grouped by date
        daily_orders = db.session.query(
            func.date(Order.created_at).label('label'),
            func.sum(Order.total_amount).label('revenue')
        ).filter(
            Order.user_id == user_id,
            Order.status == 'delivered',
            func.date(Order.created_at) >= start_date
        ).group_by('label').order_by('label').all()

        # Create a dictionary to easily access revenue by date
        daily_revenue_dict = {str(row[0]): float(row[1]) for row in daily_orders}

        # Generate a list of the last 7 dates and populate revenue, defaulting to 0
        date_list = [start_date + timedelta(days=i) for i in range(7)]
        grouped_orders = []
        for single_date in date_list:
            date_str = single_date.strftime('%Y-%m-%d')
            revenue = daily_revenue_dict.get(date_str, 0)
            grouped_orders.append((date_str, revenue))

        # Add logging here to inspect grouped_orders for daily view
        print(f"[DEBUG] Daily grouped_orders: {grouped_orders}")

    elif view == 'hourly':
        # Define timezones
        server_timezone = pytz.timezone('UTC') # Assuming server stores naive datetimes as UTC
        user_timezone = pytz.timezone('Etc/GMT-3') # EAT is GMT+3, which is Etc/GMT-3 in pytz

        start_of_day_utc = server_timezone.localize(datetime.combine(now.date(), datetime_time(0, 0, 0))).astimezone(pytz.utc)

        delivered_orders_today = db.session.execute(db.select(Order).where(
            Order.user_id == user_id,
            Order.status == 'delivered',
            Order.created_at >= start_of_day_utc # Assuming created_at is stored as UTC or convert if necessary
        )).scalars().all()

        # Group orders by hour in user's timezone
        hourly_revenue = {}
        for order in delivered_orders_today:
            # Convert timestamp to user's timezone
            # Assuming order.created_at is a timezone-aware datetime or can be localized
            # If naive, assume UTC for conversion based on server_timezone assumption above
            if order.created_at.tzinfo is None:
                 # Assume naive datetime is in server's local time, convert to UTC then user time
                 # A more robust solution would store timezone-aware datetimes
                 created_at_utc = server_timezone.localize(order.created_at).astimezone(pytz.utc)
                 created_at_user = created_at_utc.astimezone(user_timezone)
            else:
                 # If timezone-aware, just convert to user time
                 created_at_user = order.created_at.astimezone(user_timezone)

            hour_label = created_at_user.strftime('%Y-%m-%d %H:%M')
            hourly_revenue[hour_label] = hourly_revenue.get(hour_label, 0) + order.total_amount

        # Sort by hour and format for the frontend
        grouped_orders = [{'label': hour, 'revenue': revenue} for hour, revenue in sorted(hourly_revenue.items())]

    elif view == 'weekly':
        last_7_days = now - timedelta(days=7)
        grouped_orders = db.session.query(
            func.date(Order.created_at).label('label'),
            func.sum(Order.total_amount).label('revenue')
        ).filter(
            Order.user_id == user_id,
            Order.status == 'delivered',
            Order.created_at >= last_7_days
        ).group_by('label').order_by('label').all()

    else:  # Default to monthly
        grouped_orders = db.session.query(
            extract('month', Order.created_at).label('label'),
            func.sum(Order.total_amount).label('revenue')
        ).filter(
            Order.user_id == user_id,
            Order.status == 'delivered',
            extract('year', Order.created_at) == now.year
        ).group_by('label').order_by('label').all()

    # Convert SQLAlchemy results to JSON-safe dicts
    monthly_sales = []
    for row in grouped_orders:
        if view == 'hourly':
            monthly_sales.append({
                'label': row['label'],
                'revenue': float(row['revenue'])
            })
        elif view == 'monthly':
             monthly_sales.append({
                'label': calendar.month_name[int(row[0])],
                'revenue': float(row[1])
            })
        elif view in ['daily', 'weekly', 'range']:
             monthly_sales.append({
                 'label': row[0],
            'revenue': float(row[1])
             })

    # Item-level stats: quantity sold and revenue
    item_stats = {}
    delivered_orders = db.session.execute(db.select(Order).filter_by(user_id=user_id, status='delivered')).scalars().all()
    for order in delivered_orders:
        try:
            items = json.loads(order.items)
            for item in items:
                name = item['name']
                qty = item['quantity']
                revenue = item['quantity'] * item['price']
                if name not in item_stats:
                    item_stats[name] = {'quantity': 0, 'revenue': 0}
                item_stats[name]['quantity'] += qty
                item_stats[name]['revenue'] += revenue
        except Exception as e:
            print(f"Error parsing items: {e}")

    # If it's an AJAX request for a specific view, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'monthly_sales': monthly_sales,
            'item_stats': item_stats,
            'has_data': bool(monthly_sales or item_stats)
        })
    else:
        # Otherwise, render the full page
        return render_template("analytics.html",
                        monthly_sales=monthly_sales,
                        item_stats=item_stats,
                        has_data=bool(monthly_sales or item_stats))

@app.route('/export/<format>')
@login_required
def export_report(format):
    user_id = current_user.id
    orders = db.session.execute(db.select(Order).filter_by(user_id=user_id, status='delivered').order_by(Order.created_at)).scalars().all()

    if format == 'csv':
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(['Date', 'Table', 'Total Amount', 'Items'])
        for order in orders:
            cw.writerow([
                order.created_at.strftime('%Y-%m-%d %H:%M'),
                order.table_number,
                f"${order.total_amount:.2f}",
                order.items
            ])
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=report.csv"
        output.headers["Content-type"] = "text/csv"
        return output

    elif format == 'pdf':
        if not orders:
            return "No delivered orders to export.", 400
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Sales Report", ln=1, align='C')
        total_revenue = 0
        for order in orders:
            pdf.multi_cell(0, 10, f"Date: {order.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                                  f"Table: {order.table_number}\n"
                                  f"Amount: ${order.total_amount:.2f}\n"
                                  f"Items: {order.items}\n", border=1)
            total_revenue += float(order.total_amount)
        pdf.ln(5)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"Total Revenue: ${total_revenue:.2f}", ln=1, align='R')
        # Delete the delivered orders after successful export
        order_ids = [order.id for order in orders]
        if order_ids:
            from models import CommissionTransaction
            referenced_order_ids = [
                row[0] for row in db.session.execute(
                    select(CommissionTransaction.order_id).where(CommissionTransaction.order_id.in_(order_ids))
                ).all()
            ]
            deletable_order_ids = [oid for oid in order_ids if oid not in referenced_order_ids]
            if deletable_order_ids:
                db.session.execute(db.delete(Order).where(Order.id.in_(deletable_order_ids)))
                db.session.commit()
                print(f"Deleted {len(deletable_order_ids)} delivered orders after PDF export.")
            else:
                print("No delivered orders deleted (all are referenced in commission_transaction).")
        pdf_data = pdf.output(dest='S')
        if isinstance(pdf_data, bytearray):
            pdf_bytes = bytes(pdf_data)
        elif isinstance(pdf_data, bytes):
            pdf_bytes = pdf_data
        else:
            pdf_bytes = pdf_data.encode('latin1')
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=orders_report.pdf'
        return response

    return "Invalid format", 400

@app.route('/payment/<int:order_id>', methods=['GET', 'POST'])
def payment(order_id):
    # Use context-managed session for all DB operations
    with Session() as session:
        order = session.get(Order, order_id)
        if not order:
            abort(404)
        if request.method == 'POST':
            # Directly mark the order as paid without M-Pesa integration
            order.status = 'paid'
            print(f"[ORDER STATUS] Order {order.id} status changed to 'paid' at {datetime.now()}")
            session.commit()
            # Redirect to success page
            return redirect(url_for('payment_success', order_id=order_id))
        return render_template('payment.html', order=order, user=order.user)


@app.route('/payment-success/<int:order_id>')
# Removed @login_required to allow public access
def payment_success(order_id):
    # You can customize this logic as needed
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)
    user = order.user
    return render_template('payment_success.html', order=order, user=user)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_panel_required
def settings():
    from werkzeug.security import check_password_hash, generate_password_hash
    if request.method == 'POST':
        form = SettingsForm()
    else:
        form = SettingsForm(obj=current_user)
    if form.validate_on_submit():
        # Update payment settings
        current_user.payment_method = form.payment_method.data
        if form.payment_method.data == 'manual':
            current_user.mpesa_receiving_method = form.mpesa_receiving_method.data
            if form.mpesa_receiving_method.data == 'paybill':
                current_user.mpesa_paybill = form.mpesa_paybill.data
                current_user.mpesa_till = None
                current_user.mpesa_phone_receiver = None
            elif form.mpesa_receiving_method.data == 'till':
                current_user.mpesa_till = form.mpesa_till.data
                current_user.mpesa_paybill = None
                current_user.mpesa_phone_receiver = None
            elif form.mpesa_receiving_method.data == 'phone':
                current_user.mpesa_phone_receiver = form.mpesa_phone_receiver.data
                current_user.mpesa_paybill = None
                current_user.mpesa_till = None
        # Update display settings
        current_user.theme_color = form.theme_color.data
        current_user.menu_layout = form.menu_layout.data
        current_user.show_prices = form.show_prices.data
        current_user.show_descriptions = form.show_descriptions.data
        current_user.language = form.language.data
        current_user.timezone = form.timezone.data
        # Only handle password change if new_password or confirm_password is filled
        if form.new_password.data or form.confirm_password.data:
            if not form.current_password.data or not form.new_password.data or not form.confirm_password.data:
                flash('To change your password, fill in all password fields.', 'danger')
                return render_template('settings.html', form=form)
            if not check_password_hash(current_user.password, form.current_password.data):
                flash('Current password is incorrect.', 'danger')
                return render_template('settings.html', form=form)
            if form.new_password.data != form.confirm_password.data:
                flash('New passwords do not match.', 'danger')
                return render_template('settings.html', form=form)
            current_user.password = generate_password_hash(form.new_password.data)
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('settings'))
    else:
        if request.method == 'POST':
            flash('There was an error saving your settings. Please check the form and try again.', 'danger')
            print(form.errors)
    return render_template('settings.html', form=form)

@app.route('/restaurants')
def list_restaurants():
    """
    Displays a list of all registered restaurants.
    """
    # Get all restaurants (non-admin users)
    restaurants = db.session.execute(db.select(User).filter_by(is_admin=False)).scalars().all()
    
    # Format restaurant data for template
    formatted_restaurants = []
    for restaurant in restaurants:
        # Parse social media links if they exist
        social_media_links = []
        if restaurant.social_media:
            try:
                social_media_data = json.loads(restaurant.social_media)
                if isinstance(social_media_data, dict):
                    for name, url in social_media_data.items():
                        social_media_links.append({
                            'name': name,
                            'url': url
                        })
            except json.JSONDecodeError:
                pass
        formatted_restaurants.append({
            'id': restaurant.id,
            'restaurant_name': restaurant.restaurant_name,
            'restaurant_address': restaurant.restaurant_address,
            'restaurant_description': restaurant.restaurant_description,
            'opening_hours': restaurant.opening_hours,
            'website': restaurant.website,
            'logo_filename': restaurant.logo_url,
            'social_media_links': social_media_links,
            'contact_phone': getattr(restaurant, 'contact_phone', None),
            'help_contact': getattr(restaurant, 'help_contact', None)
        })
    
    return render_template('restaurants.html', restaurants=formatted_restaurants)

@app.route('/delivery_orders')
@login_required
def view_delivery_orders():
    """
    Displays a list of delivery orders for the logged-in restaurant.
    """
    delivery_orders = db.session.execute(db.select(Order).filter_by(
        restaurant_id=current_user.id,
        order_type='delivery'
    ).order_by(Order.created_at.desc())).scalars().all()

    return render_template('delivery_orders.html', delivery_orders=delivery_orders, csrf_token=generate_csrf())

@app.route('/delivery-updates')
@login_required
def delivery_updates():
    def generate():
        from sqlalchemy.orm import scoped_session, sessionmaker
        Session = scoped_session(sessionmaker(bind=db.engine))
        session = Session()
        session.expire_all()
        try:
            last_order = session.query(Order).filter(
                Order.restaurant_id == user_id,
                Order.order_type == 'delivery'
            ).order_by(Order.created_at.desc()).first()
            last_check = last_order.created_at if last_order else datetime.now()
            # Yield initial heartbeat to send headers
            yield ': heartbeat\n\n'
            while True:
                try:
                    orders = session.query(Order).filter(
                        Order.restaurant_id == user_id,
                        Order.order_type == 'delivery',
                        Order.created_at > last_check
                    ).order_by(Order.created_at.asc()).all()
                    for order in orders:
                        try:
                            items = json.loads(order.items)
                            order_data = {
                                'id': order.id,
                                'table_number': order.table_number,
                                'items': items,
                                'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                                'total_amount': order.total_amount,
                                'status': order.status,
                                'customer_name': order.customer_name,
                                'customer_phone': order.customer_phone,
                                'delivery_address': order.delivery_address,
                                'special_instructions': order.special_instructions
                            }
                            yield f"data: {json.dumps({'type': 'new_order', 'order': order_data})}\n\n"
                        except Exception as e:
                            print(f"Error processing order: {str(e)}")
                            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                    time_module.sleep(2)
                except Exception as e:
                    print(f"Error in delivery updates stream: {str(e)}")
                    yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                    time_module.sleep(2)
        except GeneratorExit:
            print("Client disconnected from /delivery-updates")
        finally:
            session.close()
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    form = AdminLoginForm()
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    if form.validate_on_submit():
        user = db.session.execute(db.select(User).filter_by(email=form.email.data)).scalar_one_or_none()
        if user and user.is_admin and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid email or password', 'danger')
            return render_template('admin/login.html', form=form)
    
    return render_template('admin/login.html', form=form)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
@admin_panel_required
def profile():
    form = ProfileForm(request.form, obj=current_user)
    if form.validate_on_submit():
        logo_url = None
        if form.logo.data and form.logo.data.filename:
            try:
                upload_result = cloudinary.uploader.upload(form.logo.data, folder=f"logos/{current_user.email.replace('@', '_')}")
                logo_url = upload_result.get('secure_url')
            except Exception as e:
                flash(f'Logo upload failed: {str(e)}', 'danger')
                return redirect(url_for('profile'))

        current_user.restaurant_name = form.restaurant_name.data
        current_user.restaurant_description = form.restaurant_description.data
        current_user.restaurant_address = form.restaurant_address.data
        current_user.opening_hours = form.opening_hours.data
        current_user.currency = form.currency.data
        current_user.website = form.website.data
        # Save social_media as JSON string if valid, else as a single link if it's a URL or www.
        import json
        import re
        sm = form.social_media.data
        if sm:
            try:
                parsed = json.loads(sm)
                if isinstance(parsed, dict):
                    current_user.social_media = json.dumps(parsed)
                else:
                    current_user.social_media = json.dumps({"link": sm})
            except Exception:
                url = sm.strip()
                if re.match(r'^https?://', url):
                    current_user.social_media = json.dumps({"link": url})
                elif url.startswith('www.'):
                    current_user.social_media = json.dumps({"link": f"https://{url}"})
                else:
                    current_user.social_media = ''
        else:
            current_user.social_media = ''
        # Save contact fields
        current_user.contact_phone = form.contact_phone.data
        current_user.help_contact = form.help_contact.data
        if logo_url:
            current_user.logo_url = logo_url
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html', form=form)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('home'))
    
    # Validate CSRF token for JSON requests
    if request.is_json:
        csrf_token = request.headers.get('X-CSRF-Token') or request.headers.get('X-Csrftoken')
        if not csrf_token:
            return jsonify({'success': False, 'error': 'CSRF token missing'}), 400
        try:
            validate_csrf(csrf_token)
            app.logger.debug(f"CSRF token validated successfully: {csrf_token[:10]}...")
        except Exception as e:
            app.logger.error(f"CSRF token validation failed: {str(e)}")
            return jsonify({'success': False, 'error': f'Invalid CSRF token: {str(e)}'}), 400
    
    # Get statistics (use counts)
    total_restaurants = db.session.execute(
        db.select(func.count()).select_from(User).where(User.is_admin == False)
    ).scalar() or 0
    total_orders = db.session.execute(
        db.select(func.count()).select_from(Order)
    ).scalar() or 0
    # Only count menu items for existing, non-admin users
    total_menu_items = db.session.execute(
        db.select(func.count()).select_from(MenuItem).join(User, MenuItem.user_id == User.id).where(User.is_admin == False)
    ).scalar() or 0
    
    # Get all restaurants
    restaurants = db.session.execute(db.select(User).filter_by(is_admin=False)).scalars().all()
    
    # --- Analytics: users at menu item limit ---

    users_at_limit = 0
    
    if request.is_json:
        return jsonify({
            'success': True,
            'data': {
                'total_restaurants': total_restaurants,
                'total_orders': total_orders,
                'total_menu_items': total_menu_items,
                'restaurants': [
                    {
                        'id': r.id,
                        'name': r.restaurant_name,
                        'email': r.email,
                        'contact': r.contact_phone,
                        'menu_items': len(r.menu_items),
                        'orders': len(r.orders)
                    } for r in restaurants
                ]
            }
        })
    
    # Generate CSRF token for template
    csrf_token = generate_csrf()
    
    return render_template('admin/dashboard.html',
                         total_restaurants=total_restaurants,
                         total_orders=total_orders,
                         total_menu_items=total_menu_items,
                         restaurants=restaurants,
                         users_at_limit=users_at_limit,
                         csrf_token=csrf_token)

@app.route('/admin/restaurant/<int:restaurant_id>')
@login_required
def admin_view_restaurant(restaurant_id):
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('home'))
    
    # Validate CSRF token for JSON requests
    if request.is_json:
        csrf_token = request.headers.get('X-CSRF-Token') or request.headers.get('X-Csrftoken')
        if not csrf_token:
            return jsonify({'success': False, 'error': 'CSRF token missing'}), 400
        try:
            validate_csrf(csrf_token)
            app.logger.debug(f"CSRF token validated successfully: {csrf_token[:10]}...")
        except Exception as e:
            app.logger.error(f"CSRF token validation failed: {str(e)}")
            return jsonify({'success': False, 'error': f'Invalid CSRF token: {str(e)}'}), 400
    
            restaurant = db.session.get(User, restaurant_id)
            if not restaurant:
                return jsonify({'success': False, 'error': 'Restaurant not found'}), 404
    
    if request.is_json:
        return jsonify({
            'success': True,
            'data': {
                'id': restaurant.id,
                'name': restaurant.restaurant_name,
                'email': restaurant.email,
                'contact': restaurant.contact_phone,
                'menu_items': [
                    {
                        'id': item.id,
                        'name': item.name,
                        'price': item.price,
                        'stock': item.stock,
                        'description': item.description
                    } for item in restaurant.menu_items
                ],
                'orders': [
                    {
                        'id': order.id,
                        'created_at': order.created_at.isoformat(),
                        'total_amount': order.total_amount,
                        'status': order.status,
                        'order_type': order.order_type
                    } for order in restaurant.orders
                ]
            }
        })
    return render_template('admin/restaurant_detail.html', restaurant=restaurant)

@app.route('/admin/restaurant/<int:restaurant_id>/delete', methods=['POST'])
@login_required
def admin_delete_restaurant(restaurant_id):
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('home'))

    # Validate CSRF token
    if request.is_json:
        csrf_token = request.headers.get('X-CSRF-Token') or request.headers.get('X-Csrftoken')
        if not csrf_token:
            return jsonify({'success': False, 'error': 'CSRF token missing'}), 400
        try:
            validate_csrf(csrf_token)
            app.logger.debug(f"CSRF token validated successfully: {csrf_token[:10]}...")
        except Exception as e:
            app.logger.error(f"CSRF token validation failed: {str(e)}")
            return jsonify({'success': False, 'error': f'Invalid CSRF token: {str(e)}'}), 400

    # 1. Find all menu item IDs for this restaurant
            menu_item_ids = [item.id for item in db.session.execute(db.select(MenuItem).filter_by(user_id=restaurant_id)).scalars().all()]
    from models import OrderItem, Feedback

    # 2. Bulk delete all order items for these menu items
    if menu_item_ids:
        db.session.execute(db.delete(OrderItem).where(OrderItem.menu_item_id.in_(menu_item_ids)))

    # 3. Bulk delete all menu items
        db.session.execute(db.delete(MenuItem).where(MenuItem.user_id == restaurant_id))

    # 4. Bulk delete all orders
        db.session.execute(db.delete(Order).where(Order.user_id == restaurant_id))

    # 5. Bulk delete Daraja credentials
        db.session.execute(db.delete(DarajaCredentials).where(DarajaCredentials.user_id == restaurant_id))

    # 5.1 Bulk delete feedback for this user
        db.session.execute(db.delete(Feedback).where(Feedback.user_id == restaurant_id))

    # 6. Bulk delete the restaurant itself
        db.session.execute(db.delete(User).where(User.id == restaurant_id))

    db.session.commit()

    if request.is_json:
        return jsonify({'success': True, 'message': 'Restaurant deleted successfully'}), 200
    return redirect(url_for('admin_dashboard'))

# Admin: Manage Help Info
@app.route('/admin/help-info', methods=['GET', 'POST'])
@login_required
def admin_help_info():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('home'))
    
    form = HelpInfoForm()
    help_info = db.session.execute(db.select(HelpInfo)).scalar_one_or_none()
    
    if form.validate_on_submit():
        if not help_info:
            help_info = HelpInfo(
                email=form.email.data,
                phone=form.phone.data,
                other=form.other.data
            )
            db.session.add(help_info)
        else:
            help_info.email = form.email.data
            help_info.phone = form.phone.data
            help_info.other = form.other.data
        db.session.commit()
        flash('Help information updated!', 'success')
        return redirect(url_for('admin_help_info'))
    
    # Pre-populate form if GET or validation failed
    if help_info:
        form.email.data = help_info.email
        form.phone.data = help_info.phone
        form.other.data = help_info.other
    
    return render_template('admin/help_info.html', form=form, help_info=help_info)

# Admin: View Feedback
@app.route('/admin/feedback')
@login_required
def admin_feedback():
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('home'))
    feedbacks = db.session.execute(db.select(Feedback).order_by(Feedback.created_at.desc())).scalars().all()
    return render_template('admin/feedback.html', feedbacks=feedbacks)

@app.route('/help')
@login_required
@admin_panel_required
def help_info():
    help_info = db.session.execute(db.select(HelpInfo)).scalar_one_or_none()
    return render_template('help.html', help_info=help_info)

@app.route('/feedback', methods=['GET', 'POST'])
@login_required
@admin_panel_required
def feedback():
    form = FeedbackForm()
    if form.validate_on_submit():
        user_id = current_user.id if hasattr(current_user, 'id') and current_user.is_authenticated else None
        fb = Feedback(user_id=user_id, email=form.email.data, message=form.message.data)
        db.session.add(fb)
        db.session.commit()
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('feedback'))
    return render_template('feedback.html', form=form)

@app.route('/admin/logout')
def admin_logout():
    return redirect(url_for('logout'))

from collections import defaultdict
import queue

menu_update_subscribers = defaultdict(list)  # {user_id: [Queue, ...]}

@app.route('/menu-updates')
@login_required
def menu_updates():
    user_id = current_user.id
    q = queue.Queue()
    menu_update_subscribers[user_id].append(q)

    def gen():
        try:
            # Yield initial heartbeat to send headers
            yield ': heartbeat\n\n'
            while True:
                data = q.get()
                yield f"data: {json.dumps(data)}\n\n"
        except GeneratorExit:
            pass
        finally:
            menu_update_subscribers[user_id].remove(q)
    return Response(stream_with_context(gen()), mimetype='text/event-stream')

def broadcast_menu_update(user_id, event):
    for q in menu_update_subscribers.get(user_id, []):
        try:
            q.put_nowait(event)
        except Exception as e:
            app.logger.error(f"Error broadcasting menu update: {str(e)}")

@app.route('/update_stock', methods=['POST'])
@login_required
def update_stock():
    try:
        # Validate CSRF token for form requests
        if not request.is_json:
            form = DeleteForm()  # Using DeleteForm since it has CSRF protection
            if not form.validate_on_submit():
                return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 400
        
        # Validate CSRF token for JSON requests
        if request.is_json:
            # Try both header names (case-insensitive)
            csrf_token = request.headers.get('X-CSRF-Token') or request.headers.get('X-Csrftoken')
            if not csrf_token:
                app.logger.warning(f"CSRF token missing in headers: {dict(request.headers)}")
                return jsonify({'success': False, 'error': 'CSRF token missing'}), 400
            try:
                validate_csrf(csrf_token)
                app.logger.debug(f"CSRF token validated successfully: {csrf_token[:10]}...")
            except Exception as e:
                app.logger.error(f"CSRF token validation failed: {str(e)}")
                return jsonify({'success': False, 'error': f'Invalid CSRF token: {str(e)}'}), 400

        item_id = request.form.get('item_id') or request.json.get('item_id')
        new_stock = request.form.get('new_stock') or request.json.get('new_stock')

        if not item_id or not new_stock:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        try:
            new_stock = int(new_stock)
        except ValueError:
            return jsonify({'success': False, 'error': 'Stock must be a number'}), 400

        menu_item = db.session.get(MenuItem, item_id)
        if not menu_item:
            return jsonify({'success': False, 'error': 'Menu item not found'}), 404

        if menu_item.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403

        menu_item.stock = new_stock
        db.session.commit()
        broadcast_menu_update(menu_item.user_id, {'type': 'stock_update', 'item_id': item_id, 'new_stock': new_stock})
        return jsonify({'success': True, 'message': 'Stock updated successfully'}), 200

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating stock: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/update_order_status/<int:order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    try:
        # Validate CSRF token for JSON requests
        if request.is_json:
            csrf_token = request.headers.get('X-CSRFToken') or request.headers.get('X-CSRF-Token') or request.headers.get('X-Csrftoken')
            if not csrf_token:
                app.logger.warning(f"CSRF token missing in headers: {dict(request.headers)}")
                return jsonify({'success': False, 'error': 'CSRF token missing'}), 400
            try:
                validate_csrf(csrf_token)
            except Exception as e:
                app.logger.error(f"CSRF token validation failed: {str(e)}")
                return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 400

        from sqlalchemy.orm import scoped_session, sessionmaker
        Session = scoped_session(sessionmaker(bind=db.engine))
        with Session() as session:
            order = session.get(Order, order_id)
            if not order:
                return jsonify({'error': 'Order not found'}), 404
            if order.user_id != current_user.id:
                return jsonify({'error': 'Unauthorized'}), 403
            new_status = request.json.get('status')
            if not new_status:
                return jsonify({'error': 'Status is required'}), 400
            # Add pending_confirmation to valid statuses
            valid_statuses = ['new', 'pending', 'pending_confirmation', 'paid', 'preparing', 'ready', 'delivered', 'cancelled']
            if new_status not in valid_statuses:
                return jsonify({'error': f'Invalid status: {new_status}'}), 400
            if order.status == 'delivered':
                return jsonify({'error': 'Cannot change status of a delivered order'}), 400
            status_order = {s: i for i, s in enumerate(valid_statuses)}
            if status_order.get(new_status, -1) < status_order.get(order.status, -1) and new_status != 'cancelled':
                return jsonify({'error': f'Cannot move status backward from {order.status} to {new_status}'}), 400

            # --- ENFORCE PAYMENT BEFORE PREPARATION FOR MANUAL ORDERS ---
            # If payment method is manual, require 'paid' before 'preparing', 'preparing' before 'ready', 'ready' before 'delivered'
            restaurant = session.get(User, order.restaurant_id)
            is_manual = getattr(restaurant, 'payment_method', 'manual') == 'manual'
            if is_manual:
                if new_status == 'preparing' and order.status not in ['paid', 'pending_confirmation']:
                    return jsonify({'error': 'Order must be marked as paid before it can be prepared.'}), 400
                if new_status == 'ready' and order.status != 'preparing':
                    return jsonify({'error': 'Order must be in preparing status before it can be marked as ready.'}), 400
                if new_status == 'delivered' and order.status != 'ready':
                    return jsonify({'error': 'Order must be ready before it can be delivered.'}), 400

            # Handle order cancellation
            if new_status == 'cancelled':
                if order.status in ['pending', 'pending_confirmation', 'paid', 'preparing', 'ready', 'new']:
                    try:
                        items = json.loads(order.items)
                        for item in items:
                            menu_item = session.get(MenuItem, item.get('item_id'))
                            if menu_item and menu_item.user_id == current_user.id:
                                menu_item.stock += item['quantity']
                                broadcast_menu_update(menu_item.user_id, {
                                    'type': 'stock_update',
                                    'item_id': menu_item.id,
                                    'new_stock': menu_item.stock
                                })
                            else:
                                app.logger.error(f"MenuItem not found for item_id={item.get('item_id')} (user_id={current_user.id})")
                        order.status = 'cancelled'
                        print(f"[ORDER STATUS] Order {order.id} status changed to 'cancelled' at {datetime.now()}")
                        session.commit()
                        return jsonify({'success': True, 'status': new_status})
                    except Exception as e:
                        session.rollback()
                        return jsonify({'error': f'Failed to cancel order: {str(e)}'}), 500
                else:
                    return jsonify({'error': 'Order can only be cancelled before delivery'}), 400
            else:
                # Only update if status is actually changing
                if order.status != new_status:
                    order.status = new_status
                    print(f"[ORDER STATUS] Order {order.id} status changed to '{new_status}' at {datetime.now()}")
                    session.commit()
                    # --- IMMEDIATE SOCKETIO BROADCAST ---
                    from flask_socketio import SocketIO, emit
                    # Prepare order data for broadcast (adjust fields as needed)
                    order_data = {
                        'id': order.id,
                        'status': order.status,
                        'table_number': order.table_number,
                        'items': order.items,
                        'special_instructions': order.special_instructions,
                        'user_id': order.user_id,
                        'restaurant_id': order.restaurant_id,
                        'updated_at': order.updated_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(order, 'updated_at') else None,
                        'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(order, 'created_at') else None,
                        'total_amount': order.total_amount
                    }
                    # Emit to the user's order room
                    socketio.emit('order_update', order_data, room=f'order_{order.user_id}')
                    # Do not return here; further logic (like stock decrement on delivered)
                    # must execute before sending the final response

                    # Cancel auto-transition timer if it exists
                    try:
                        global auto_transition_timers
                        if order.id in auto_transition_timers:
                            auto_transition_timers[order.id].cancel()
                            del auto_transition_timers[order.id]
                            print(f"[ORDER STATUS] Cancelled auto-transition timer for order {order.id}")
                    except Exception as e:
                        print(f"[ORDER STATUS] Error cancelling auto-transition timer: {str(e)}")
                    
                    session.commit()
                    if new_status == 'delivered':
                        try:
                            items = json.loads(order.items)
                            for item in items:
                                menu_item = session.get(MenuItem, item.get('item_id'))
                                if menu_item and menu_item.user_id == current_user.id:
                                    menu_item.stock = max(0, menu_item.stock - item['quantity'])
                                    session.commit()
                                    app.logger.info(f"Decremented stock for item_id={menu_item.id}: new stock={menu_item.stock}")
                                    broadcast_menu_update(menu_item.user_id, {
                                        'type': 'stock_update',
                                        'item_id': menu_item.id,
                                        'new_stock': menu_item.stock
                                    })
                                else:
                                    app.logger.error(f"MenuItem not found for item_id={item.get('item_id')} (user_id={current_user.id})")
                        except Exception as e:
                            app.logger.error(f"Error decrementing stock or broadcasting: {str(e)}")
                        try:
                            if new_status == 'ready':
                                notify_hardware({"status": "ready"})
                            elif new_status == 'delivered':
                                notify_hardware({"status": "delivered"})
                        except Exception as e:
                            print(f"Error triggering hardware notification: {str(e)}")
                        return jsonify({'success': True, 'status': new_status})
                    else:
                        # For non-delivered statuses, return success after broadcast
                        return jsonify({'success': True, 'status': new_status})
    except Exception as e:
        app.logger.error(f"Error in update_order_status: {str(e)}")
        try:
            db.session.remove()
        except Exception:
            pass
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/daraja-settings', methods=['GET', 'POST'])
@login_required
@admin_panel_required
def daraja_settings():
    form = DarajaCredentialsForm()
    credentials = db.session.execute(db.select(DarajaCredentials).filter_by(user_id=current_user.id)).scalar_one_or_none()
    if form.validate_on_submit():
        if credentials:
            credentials.consumer_key = form.consumer_key.data
            credentials.consumer_secret = form.consumer_secret.data
            credentials.shortcode = form.shortcode.data
            credentials.passkey = form.passkey.data
            credentials.environment = form.environment.data
        else:
            credentials = DarajaCredentials(
                user_id=current_user.id,
                consumer_key=form.consumer_key.data,
                consumer_secret=form.consumer_secret.data,
                shortcode=form.shortcode.data,
                passkey=form.passkey.data,
                environment=form.environment.data
            )
            db.session.add(credentials)
        db.session.commit()
        flash('M-Pesa credentials saved successfully!', 'success')
        return redirect(url_for('daraja_settings'))
    if credentials:
        form.consumer_key.data = credentials.consumer_key
        form.consumer_secret.data = credentials.consumer_secret
        form.shortcode.data = credentials.shortcode
        form.passkey.data = credentials.passkey
        form.environment.data = credentials.environment
    return render_template('daraja_settings.html', form=form)

@app.route('/test-daraja-credentials', methods=['POST'])
@login_required
def test_daraja_credentials():
    data = request.get_json()
    
    # Create a temporary credentials object for testing
    test_credentials = DarajaCredentials(
        consumer_key=data['consumer_key'],
        consumer_secret=data['consumer_secret'],
        shortcode=data['shortcode'],
        passkey=data['passkey'],
        environment=data['environment']
    )
    
    success, message = test_credentials(test_credentials)
    return jsonify({'success': success, 'message': message})

# Update the payment route to use restaurant-specific credentials
@app.route('/process-payment', methods=['POST'])
# @login_required  # Removed to allow unauthenticated access
def process_payment():
    from models import Order, User, DarajaCredentials  # Ensure imports for model lookups
    data = request.get_json()
    phone = data.get('phone')
    amount = data.get('amount')
    order_id = data.get('order_id')
    restaurant_id = data.get('restaurant_id')

    # Try to infer restaurant_id from order if not provided
    if not restaurant_id and order_id:
        order = db.session.get(Order, order_id)
        if order:
            restaurant_id = order.restaurant_id
        else:
            return jsonify({'success': False, 'message': 'Order not found.'}), 400

    if not restaurant_id:
        return jsonify({'success': False, 'message': 'Missing restaurant_id.'}), 400

    # Get restaurant's payment settings and credentials
    restaurant = db.session.get(User, restaurant_id)
    if not restaurant:
        return jsonify({'success': False, 'message': 'Restaurant not found.'}), 400
    credentials = db.session.execute(db.select(DarajaCredentials).filter_by(user_id=restaurant_id)).scalar_one_or_none()
    manual_payment_details = None

    # Check if STK push is enabled and credentials exist
    if getattr(restaurant, 'payment_method', None) == 'stk_push' and credentials:
        try:
            # Initiate STK push with restaurant's credentials
            response = stk_push(
                phone=phone,
                amount=amount,
                account_reference=str(order_id),
                transaction_desc=f"Payment for order {order_id}",
                credentials=credentials
            )

            if response.get('ResponseCode') == '0':
                return jsonify({
                    'success': True,
                    'message': 'Payment initiated successfully',
                    'checkout_request_id': response.get('CheckoutRequestID'),
                    'payment_method': 'stk_push'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': response.get('ResponseDescription', 'Payment initiation failed')
                }), 400

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error processing payment: {str(e)}'
            }), 500

    # If STK push is not enabled or failed, use manual payment
    if getattr(restaurant, 'mpesa_number', None):
        manual_payment_details = {
            'type': 'phone',
            'number': restaurant.mpesa_number
        }
    elif getattr(restaurant, 'mpesa_paybill', None):
        manual_payment_details = {
            'type': 'paybill',
            'number': restaurant.mpesa_paybill
        }
    elif getattr(restaurant, 'mpesa_till', None):
        manual_payment_details = {
            'type': 'till',
            'number': restaurant.mpesa_till
        }

    if manual_payment_details:
        return jsonify({
            'success': True,
            'message': 'Manual payment details retrieved successfully',
            'payment_method': 'manual',
            'payment_details': manual_payment_details,
            'amount': amount,
            'order_id': order_id
        })
    else:
        return jsonify({
            'success': False,
            'message': 'No payment details configured. Please contact the restaurant.'
        }), 400

@app.route('/admin/platform-settings', methods=['GET', 'POST'])
@login_required
def platform_settings():
    if not current_user.is_admin:
        abort(403)
    settings = db.session.execute(db.select(PlatformSettings)).scalar_one_or_none()
    if not settings:
        settings = PlatformSettings()
        db.session.add(settings)
        db.session.commit()
    form = PlatformSettingsForm(obj=settings)
    if form.validate_on_submit():
        settings.callback_url_sandbox = form.callback_url_sandbox.data
        settings.callback_url_production = form.callback_url_production.data
        db.session.commit()
        flash('Platform settings updated!', 'success')
        return redirect(url_for('platform_settings'))
    return render_template('admin/platform_settings.html', form=form)

@app.route('/initiate-payment', methods=['POST'])
def initiate_payment():
    data = request.get_json()
    app.logger.info(f"[INITIATE PAYMENT] Incoming payload: {data}")
    phone = data.get('phone')
    order_data = data.get('order_data')
    if not phone or not order_data:
        app.logger.error("[INITIATE PAYMENT] Missing phone or order_data")
        return jsonify({'success': False, 'message': 'Missing phone or order data'}), 400
    restaurant_id = order_data.get('restaurant_id')
    if not restaurant_id:
        app.logger.error("[INITIATE PAYMENT] Missing restaurant_id in order_data")
        return jsonify({'success': False, 'message': 'Missing restaurant_id in order data'}), 400
    # Fetch restaurant and payment method
    from models import User, DarajaCredentials
    restaurant = db.session.get(User, restaurant_id)
    if not restaurant:
        app.logger.error(f"[INITIATE PAYMENT] Restaurant not found for restaurant_id={restaurant_id}")
        return jsonify({'success': False, 'message': 'Restaurant not found'}), 400
    payment_method = getattr(restaurant, 'payment_method', 'manual')
    creds = db.session.execute(db.select(DarajaCredentials).filter_by(user_id=restaurant_id)).scalar_one_or_none()

    if payment_method == 'stk_push' and creds:
        app.logger.info(f"[INITIATE PAYMENT] Found Daraja credentials for restaurant_id={restaurant_id}")
        try:
            from mpesa_utils import stk_push
            amount = order_data.get('total_amount')
            import secrets
            session_token = secrets.token_urlsafe(16)
            response = stk_push(phone, amount, session_token, f"Order payment for restaurant {restaurant_id}", creds)
            app.logger.info(f"[INITIATE PAYMENT] STK Push response: {response}")
            if 'errorCode' in response:
                app.logger.error(f"[INITIATE PAYMENT] STK Push error: {response}")
                return jsonify({'success': False, 'message': response.get('errorMessage', 'Payment initiation failed')}), 400
            from models import PendingPayment
            import json
            pending = PendingPayment(
                session_token=session_token,
                order_data=json.dumps(order_data),
                phone=phone
            )
            db.session.add(pending)
            db.session.commit()
            return jsonify({'success': True, 'session_token': session_token})
        except Exception as e:
            app.logger.exception(f"[INITIATE PAYMENT] Exception during STK Push: {e}")
            return jsonify({'success': False, 'message': 'Payment initiation failed'}), 400
    elif payment_method == 'manual':
        manual_payment_details = None
        if getattr(restaurant, 'mpesa_number', None):
            manual_payment_details = {'type': 'phone', 'number': restaurant.mpesa_number}
        elif getattr(restaurant, 'mpesa_paybill', None):
            manual_payment_details = {'type': 'paybill', 'number': restaurant.mpesa_paybill}
        elif getattr(restaurant, 'mpesa_till', None):
            manual_payment_details = {'type': 'till', 'number': restaurant.mpesa_till}
        if manual_payment_details:
            return jsonify({
                'success': True,
                'payment_method': 'manual',
                'payment_details': manual_payment_details,
                'amount': order_data.get('total_amount'),
                'order_id': order_data.get('order_id')
            })
        else:
            return jsonify({'success': False, 'message': 'No manual payment details configured.'}), 400
    else:
        return jsonify({'success': False, 'message': 'No valid payment method configured.'}), 400

@app.route('/payment-status')
def payment_status_poll():
    session_token = request.args.get('session')
    if not session_token:
        return jsonify({'success': False, 'message': 'Missing session token'}), 400
    pending = db.session.execute(db.select(PendingPayment).filter_by(session_token=session_token)).scalar_one_or_none()
    if not pending:
        return jsonify({'success': False, 'message': 'Session not found'}), 404
    return jsonify({'success': True, 'is_paid': pending.is_paid})

# Update mpesa_callback to create order only after payment success
@app.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    data = request.get_json(force=True)
    print('[MPESA CALLBACK] Received:', data)
    try:
        stk_callback = data.get('Body', {}).get('stkCallback', {})
        result_code = stk_callback.get('ResultCode')
        metadata = stk_callback.get('CallbackMetadata', {})
        # Find AccountReference (session_token) in metadata
        session_token = None
        for item in metadata.get('Item', []):
            if item.get('Name') == 'AccountReference':
                session_token = item.get('Value')
                break
        if session_token is None:
            print('[MPESA CALLBACK] No AccountReference found in callback')
            return {'ResultCode': 0, 'ResultDesc': 'No AccountReference, nothing updated'}
        # Only mark as paid if ResultCode == 0 (success)
        if result_code == 0:
            pending = db.session.execute(db.select(PendingPayment).filter_by(session_token=session_token)).scalar_one_or_none()
            if pending and not pending.is_paid:
                # Create the order in the DB
                order_data = json.loads(pending.order_data)
                from models import Order
                new_order = Order(
                    table_number=order_data.get('table_number'),
                    items=json.dumps(order_data.get('items', [])),
                    special_instructions=order_data.get('special_instructions', ''),
                    user_id=order_data.get('restaurant_id'),
                    restaurant_id=order_data.get('restaurant_id'),
                    total_amount=order_data.get('total_amount'),
                    order_type=order_data.get('order_type', 'dine_in'),
                    customer_name=order_data.get('customer_name', ''),
                    customer_phone=order_data.get('customer_phone', ''),
                    delivery_address=order_data.get('delivery_address', '')
                )
                db.session.add(new_order)
                pending.is_paid = True
                db.session.commit()
                print(f'[MPESA CALLBACK] Order {new_order.id} created and marked as paid')
                # Optionally: notify restaurant via SocketIO/SSE here
            else:
                print(f'[MPESA CALLBACK] PendingPayment not found or already paid for session_token={session_token}')
        else:
            print(f'[MPESA CALLBACK] Payment failed for session_token={session_token}, ResultCode: {result_code}')
        return {'ResultCode': 0, 'ResultDesc': 'Callback received successfully'}
    except Exception as e:
        print('[MPESA CALLBACK] Error:', str(e))
        return {'ResultCode': 1, 'ResultDesc': 'Callback processing error'}

@app.route('/payment-status-page')
def payment_status_page():
    order_id = request.args.get('order_id')
    from models import Order, User
    order = db.session.get(Order, order_id)
    user = None
    if order:
        user = db.session.get(User, order.user_id)
    return render_template('payment_status.html', order_id=order_id, user=user)


@app.route('/api/payment-status/<int:order_id>')
def api_payment_status(order_id):
    from models import Order
    from sqlalchemy.orm import scoped_session, sessionmaker
    Session = scoped_session(sessionmaker(bind=db.engine))
    with Session() as session:
        order = session.get(Order, order_id)
        if order and order.status == 'paid':
            return jsonify({'status': 'success', 'order_id': order_id})
        return jsonify({'status': 'pending'})

@app.route('/confirm-manual-payment/<int:order_id>', methods=['POST'])
def confirm_manual_payment(order_id):
    try:
        from sqlalchemy.orm import scoped_session, sessionmaker
        Session = scoped_session(sessionmaker(bind=db.engine))
        with Session() as session:
            order = session.get(Order, order_id)
            if not order:
                flash('Order not found.', 'danger')
                return redirect(url_for('dashboard'))
            
            # Only allow confirmation if order is in pending_confirmation status
            if order.status != 'pending_confirmation':
                flash('Order is not in pending confirmation status.', 'danger')
                return redirect(url_for('dashboard'))
            
            # Update status to paid
            order.status = 'paid'
            
            # Calculate and store commission
            commission_transaction = CommissionService.calculate_order_commission(order_id)
            
            session.commit()
            print(f"[ORDER STATUS] Order {order_id} manually confirmed and status changed to 'paid' at {datetime.now()}")
            
            if commission_transaction:
                flash('Payment confirmed successfully! Commission has been calculated.', 'success')
            else:
                flash('Payment confirmed successfully!', 'success')
            
            return redirect(url_for('order_success', order_id=order_id))
    except Exception as e:
        app.logger.error(f"Error confirming manual payment: {str(e)}")
        flash('Error confirming payment.', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/order-success/<int:order_id>')
def order_success(order_id):
    from models import Order, User
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)
    user = db.session.get(User, order.user_id)
    return render_template('order_success.html', order=order, user=user)


@app.route('/api/order/<int:order_id>/status', methods=['POST'])
@login_required
def update_order_status_api(order_id):
    return update_order_status(order_id)

@app.route('/api/order/<int:order_id>/confirm-payment', methods=['POST'])
@login_required
def confirm_payment_api(order_id):
    """API endpoint to confirm payment for pending_confirmation orders"""
    try:
        from sqlalchemy.orm import scoped_session, sessionmaker
        Session = scoped_session(sessionmaker(bind=db.engine))
        with Session() as session:
            order = session.get(Order, order_id)
            if not order:
                return jsonify({'success': False, 'error': 'Order not found'}), 404
            
            if order.user_id != current_user.id:
                return jsonify({'success': False, 'error': 'Unauthorized'}), 403
            
            # Only allow confirmation if order is in pending_confirmation status
            if order.status != 'pending_confirmation':
                return jsonify({'success': False, 'error': 'Order is not in pending confirmation status'}), 400
            
            # Update status to paid
            order.status = 'paid'
            
            # Calculate and store commission
            commission_transaction = CommissionService.calculate_order_commission(order_id)
            
            session.commit()
            print(f"[ORDER STATUS] Order {order_id} payment confirmed and status changed to 'paid' at {datetime.now()}")
            
            message = 'Payment confirmed successfully'
            if commission_transaction:
                message += ' and commission calculated'
            
            return jsonify({'success': True, 'status': 'paid', 'message': message})
    except Exception as e:
        app.logger.error(f"Error confirming payment: {str(e)}")
        return jsonify({'success': False, 'error': f'Internal server error: {str(e)}'}), 500

# Category Form
class CategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description')

# Delete Form (for CSRF protection)
class DeleteForm(FlaskForm):
    pass


@app.route('/admin/categories', methods=['GET', 'POST'])
def admin_categories():
    form = CategoryForm()
    delete_form = DeleteForm()
    if form.validate_on_submit():
        name = form.name.data.strip()
        description = form.description.data.strip() if form.description.data else None
        if db.session.execute(db.select(Category).filter_by(name=name)).scalar_one_or_none():
            flash('Category with this name already exists.', 'warning')
        else:
            category = Category(name=name, description=description)
            db.session.add(category)
            db.session.commit()
            flash('Category added successfully!', 'success')
        return redirect(url_for('admin_categories'))
    categories = db.session.execute(db.select(Category)).scalars().all()
    return render_template('admin/categories.html', form=form, categories=categories, delete_form=delete_form)

@app.route('/admin/categories/edit/<int:category_id>', methods=['GET', 'POST'])
def admin_edit_category(category_id):
    category = db.session.get(Category, category_id)
    if not category:
        abort(404)
    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        category.name = form.name.data.strip()
        category.description = form.description.data.strip() if form.description.data else None
        db.session.commit()
        flash('Category updated successfully!', 'success')
        return redirect(url_for('admin_categories'))
    return render_template('admin/edit_category.html', form=form, category=category)

@app.route('/admin/categories/delete/<int:category_id>', methods=['POST'])
def admin_delete_category(category_id):
    form = DeleteForm()
    if form.validate_on_submit():
        category = db.session.get(Category, category_id)
        if not category:
            flash('Category not found.', 'danger')
            return redirect(url_for('admin_categories'))
        db.session.delete(category)
        db.session.commit()
        flash('Category deleted successfully!', 'success')
    return redirect(url_for('admin_categories'))

def get_currency_symbol(currency):
    symbols = {
        'USD': '$',
        'KES': 'KSh',
        'EUR': '€',
        'GBP': '£',
        'INR': '₹',
        'AUD': 'A$',
        'CAD': 'C$',
        'JPY': '¥'
    }
    return symbols.get(currency, '$')

# Initialize SocketIO with gevent async mode and CORS support
import sys

if sys.platform == "win32":
    async_mode = "threading"
else:
    async_mode = "gevent"

socketio = SocketIO(app, async_mode=async_mode, cors_allowed_origins="*")

# Global variable to store auto-transition timers
auto_transition_timers = {}

# Global shutdown flag
shutdown_requested = False

def cleanup_on_shutdown():
    """Clean up all resources when shutting down"""
    global shutdown_requested, auto_transition_timers
    
    if shutdown_requested:
        return  # Already cleaning up
    
    shutdown_requested = True
    app.logger.info("Shutdown requested, cleaning up resources...")
    
    # Cancel all auto-transition timers
    app.logger.info(f"Cancelling {len(auto_transition_timers)} auto-transition timers...")
    for order_id, timer in list(auto_transition_timers.items()):
        try:
            if hasattr(timer, 'cancel'):
                timer.cancel()
            app.logger.info(f"Cancelled timer for order {order_id}")
        except Exception as e:
            logger.warning(f"Error cancelling timer for order {order_id}: {e}")
    auto_transition_timers.clear()
    
    # Clean up hardware notifier
    try:
        cleanup_hardware_notifier()
        app.logger.info("Hardware notifier cleaned up")
    except Exception as e:
        logger.warning(f"Error cleaning up hardware notifier: {e}")
    
    # Clean up database sessions
    try:
        db.session.remove()
        app.logger.info("Database sessions cleaned up")
    except Exception as e:
        logger.warning(f"Error cleaning up database sessions: {e}")
    
    # Avoid blocking or yielding in signal context to prevent gevent errors
    app.logger.info("Cleanup completed")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    app.logger.info(f"Received signal {signum}, initiating shutdown...")
    cleanup_on_shutdown()
    # Explicitly stop the Socket.IO server and exit the process
    try:
        socketio.stop()
    except Exception:
        pass
    try:
        sys.exit(0)
    except SystemExit:
        raise

# Register signal handlers
import signal
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

# Register cleanup function to run on exit
import atexit
atexit.register(cleanup_on_shutdown)

# --- SocketIO event handlers for real-time updates ---
from threading import Thread
import functools

# Keep track of background threads for each user
user_dashboard_threads = {}
user_order_threads = {}
user_menu_threads = {}
user_delivery_threads = {}

def dashboard_update_thread(user_id):
    with app.app_context():
        from sqlalchemy.orm import scoped_session, sessionmaker
        Session = scoped_session(sessionmaker(bind=db.engine))
        session = Session()
        try:
            last_sent = None
            while not shutdown_requested:
                try:
                    pending_statuses = ['new', 'pending', 'paid', 'preparing', 'ready']
                    pending_dine_in = session.query(Order).filter(
                        Order.restaurant_id == user_id,
                        Order.status.in_(pending_statuses),
                        Order.order_type == 'dine_in',
                        Order.status != 'archived'
                    ).count()
                    pending_delivery = session.query(Order).filter(
                        Order.restaurant_id == user_id,
                        Order.status.in_(pending_statuses),
                        Order.order_type == 'delivery',
                        Order.status != 'archived'
                    ).count()
                    today = datetime.now().date()
                    delivered_orders = session.query(Order).filter(
                        Order.restaurant_id == user_id,
                        Order.status == 'delivered'
                    ).all()
                    today_delivered_orders = [
                        order for order in delivered_orders 
                        if order.created_at.date() == today
                    ]
                    today_revenue = sum(order.total_amount for order in today_delivered_orders)
                    total_orders = session.query(Order).filter(
                        Order.restaurant_id == user_id,
                        Order.status != 'archived'
                    ).count()
                    data = {
                        'pending_dine_in': pending_dine_in,
                        'pending_delivery': pending_delivery,
                        'delivered_orders': len(delivered_orders),
                        'today_revenue': format_price_filter(today_revenue, db.session.get(User, user_id).currency),
                        'total_orders': total_orders,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    if last_sent is None or json.dumps(data, sort_keys=True) != last_sent:
                        socketio.emit('dashboard_update', data, room=f'dashboard_{user_id}')
                        last_sent = json.dumps(data, sort_keys=True)
                except Exception as e:
                    socketio.emit('dashboard_update', {'type': 'error', 'message': str(e)}, room=f'dashboard_{user_id}')
                
                # Check for shutdown every 5 seconds
                for _ in range(5):
                    if shutdown_requested:
                        break
                    time_module.sleep(1)
        finally:
            session.close()

def order_update_thread(user_id):
    with app.app_context():
        from sqlalchemy.orm import scoped_session, sessionmaker
        Session = scoped_session(sessionmaker(bind=db.engine))
        session = Session()
        try:
            last_order = session.query(Order).filter(Order.restaurant_id == user_id).order_by(
                Order.created_at.desc(),
                Order.updated_at.desc()
            ).first()
            last_check = last_order.created_at if last_order else datetime.now()
            last_status_check = last_order.updated_at if last_order else datetime.now()
            
            # Track sent orders to prevent duplicates
            last_sent_orders = {}  # {order_id: (status, updated_at)}
            
            while not shutdown_requested:
                try:
                    updated_orders = session.query(Order).filter(
                        Order.restaurant_id == user_id,
                        Order.updated_at > last_status_check
                    ).order_by(Order.updated_at.asc()).all()
                    new_orders = session.query(Order).filter(
                        Order.restaurant_id == user_id,
                        Order.created_at > last_check
                    ).order_by(Order.created_at.asc()).all()
                    
                    # Filter out already sent orders
                    new_updated_orders = []
                    new_new_orders = []
                    
                    for order in updated_orders:
                        order_key = (order.id, order.status, order.updated_at)
                        if order.id not in last_sent_orders or last_sent_orders[order.id] != order_key:
                            new_updated_orders.append(order)
                            last_sent_orders[order.id] = order_key
                    
                    for order in new_orders:
                        order_key = (order.id, order.status, order.updated_at)
                        if order.id not in last_sent_orders or last_sent_orders[order.id] != order_key:
                            new_new_orders.append(order)
                            last_sent_orders[order.id] = order_key
                    
                    if new_updated_orders or new_new_orders:
                        print(f"Order updates - Found {len(new_updated_orders)} updated orders and {len(new_new_orders)} new orders")
                        for order in new_updated_orders + new_new_orders:
                            print(f"Order {order.id}: status={order.status}, type={order.order_type}, created={order.created_at}")
                    
                    if new_updated_orders or new_new_orders:
                        for order in new_updated_orders + new_new_orders:
                            try:
                                order_data = {
                                    'id': order.id,
                                    'table_number': order.table_number,
                                    'items': json.loads(order.items),
                                    'total_amount': float(order.total_amount),
                                    'created_at': order.created_at.isoformat(),
                                    'special_instructions': order.special_instructions,
                                    'status': order.status,
                                    'order_type': order.order_type,
                                    'customer_name': order.customer_name,
                                    'customer_phone': order.customer_phone,
                                    'delivery_address': order.delivery_address,
                                    'update_type': 'updated' if order in new_updated_orders else 'new',
                                    'is_delivery': order.order_type == 'delivery'
                                }
                                socketio.emit('order_update', order_data, room=f'order_{user_id}')
                            except json.JSONDecodeError:
                                continue
                        if new_orders:
                            last_check = new_orders[-1].created_at
                        if updated_orders:
                            last_status_check = updated_orders[-1].updated_at
                    
                    # Clean up old order IDs from tracking dict (keep only last 200)
                    if len(last_sent_orders) > 200:
                        # Keep only the most recent orders
                        sorted_orders = sorted(last_sent_orders.items(), key=lambda x: x[1][2], reverse=True)
                        last_sent_orders = dict(sorted_orders[:100])
                    
                    # Check for shutdown every 5 seconds
                    for _ in range(5):
                        if shutdown_requested:
                            break
                        time_module.sleep(1)
                except Exception as e:
                    socketio.emit('order_update', {'type': 'error', 'message': str(e)}, room=f'order_{user_id}')
                    time_module.sleep(5)
        finally:
            session.close()

def delivery_update_thread(user_id):
    with app.app_context():
        from sqlalchemy.orm import scoped_session, sessionmaker
        Session = scoped_session(sessionmaker(bind=db.engine))
        session = Session()
        try:
            last_order = session.query(Order).filter(
                Order.restaurant_id == user_id,
                Order.order_type == 'delivery'
            ).order_by(Order.created_at.desc()).first()
            last_check = last_order.created_at if last_order else datetime.now()
            while not shutdown_requested:
                try:
                    orders = session.query(Order).filter(
                        Order.restaurant_id == user_id,
                        Order.order_type == 'delivery',
                        Order.created_at > last_check
                    ).order_by(Order.created_at.asc()).all()
                    for order in orders:
                        try:
                            items = json.loads(order.items)
                            order_data = {
                                'id': order.id,
                                'table_number': order.table_number,
                                'items': items,
                                'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                                'total_amount': order.total_amount,
                                'status': order.status,
                                'customer_name': order.customer_name,
                                'customer_phone': order.customer_phone,
                                'delivery_address': order.delivery_address,
                                'special_instructions': order.special_instructions
                            }
                            socketio.emit('delivery_update', {'type': 'new_order', 'order': order_data}, room=f'delivery_{user_id}')
                        except Exception as e:
                            socketio.emit('delivery_update', {'type': 'error', 'message': str(e)}, room=f'delivery_{user_id}')
                    
                    # Check for shutdown every 2 seconds
                    for _ in range(2):
                        if shutdown_requested:
                            break
                        time_module.sleep(1)
                except Exception as e:
                    socketio.emit('delivery_update', {'type': 'error', 'message': str(e)}, room=f'delivery_{user_id}')
                    time_module.sleep(2)
        finally:
            session.close()

# --- SocketIO event handlers ---
@socketio.on('join_dashboard')
def handle_join_dashboard(data):
    user_id = data['user_id']
    join_room(f'dashboard_{user_id}')
    if user_id not in user_dashboard_threads:
        t = Thread(target=dashboard_update_thread, args=(user_id,), daemon=True)
        user_dashboard_threads[user_id] = t
        t.start()

@socketio.on('join_orders')
def handle_join_orders(data):
    user_id = data['user_id']
    join_room(f'order_{user_id}')
    if user_id not in user_order_threads:
        t = Thread(target=order_update_thread, args=(user_id,), daemon=True)
        user_order_threads[user_id] = t
        t.start()

@socketio.on('join_delivery')
def handle_join_delivery(data):
    user_id = data['user_id']
    join_room(f'delivery_{user_id}')
    if user_id not in user_delivery_threads:
        t = Thread(target=delivery_update_thread, args=(user_id,), daemon=True)
        user_delivery_threads[user_id] = t
        t.start()

@app.route('/download-qr')
@login_required
def download_qr():
    import requests
    from flask import send_file
    import io
    qr_url = current_user.qr_url
    if not qr_url:
        flash('QR code not available.', 'danger')
        return redirect(url_for('dashboard'))
    try:
        response = requests.get(qr_url, stream=True)
        response.raise_for_status()
        img_bytes = io.BytesIO(response.content)
        img_bytes.seek(0)
        return send_file(
            img_bytes,
            mimetype='image/png',
            as_attachment=True,
            download_name=f'{current_user.restaurant_name}_qr.png'
        )
    except Exception as e:
        flash('Failed to download QR code.', 'danger')
        return redirect(url_for('dashboard'))



# --- Menu updates: broadcast via SocketIO ---
# This is the ONLY broadcast_menu_update function that should be used.
def broadcast_menu_update(user_id, event):
    socketio.emit('menu_update', event, room=f'menu_{user_id}')

@socketio.on('join_menu')
def handle_join_menu(data):
    user_id = data['user_id']
    join_room(f'menu_{user_id}')

@app.route('/csrf-token', methods=['GET'])
def get_csrf_token():
    token = generate_csrf()
    resp = make_response(jsonify({'csrf_token': token}))
    resp.set_cookie('XSRF-TOKEN', token)
    return resp


@app.route('/admin-panel')
@login_required
@admin_panel_required
def admin_panel():
    return render_template('admin_panel.html')

@app.route('/set-admin-panel-password', methods=['GET', 'POST'])
@login_required
def set_admin_panel_password():
    if current_user.admin_panel_password_hash:
        # Already set, redirect to enter password
        return redirect(url_for('admin_panel_password'))
    form = SetAdminPanelPasswordForm()
    if form.validate_on_submit():
        current_user.admin_panel_password_hash = generate_password_hash(form.password.data)
        from extensions import db
        db.session.commit()
        flash('Admin panel password set! Please enter it to continue.', 'success')
        return redirect(url_for('admin_panel_password'))
    return render_template('set_admin_panel_password.html', form=form)

@app.route('/admin-panel-password', methods=['GET', 'POST'])
@login_required
def admin_panel_password():
    if not current_user.admin_panel_password_hash:
        return redirect(url_for('set_admin_panel_password'))
    form = AdminPanelPasswordForm()
    if 'admin_panel_failed_attempts' not in session:
        session['admin_panel_failed_attempts'] = 0
    if form.validate_on_submit():
        if check_password_hash(current_user.admin_panel_password_hash, form.password.data):
            session['admin_panel_authenticated'] = True
            session['admin_panel_failed_attempts'] = 0
            flash('Admin panel access granted.', 'success')
            next_page = request.args.get('next') or url_for('admin_panel')
            return redirect(next_page)
        else:
            session['admin_panel_failed_attempts'] += 1
            flash('Incorrect admin panel password.', 'danger')
            if session['admin_panel_failed_attempts'] >= 3:
                flash('Warning: 3 or more failed attempts. Consider resetting your admin panel password.', 'warning')
            # Optionally log to server
            app.logger.warning(f"Failed admin panel password attempt for user {current_user.id} (total: {session['admin_panel_failed_attempts']})")
    return render_template('admin_panel_password.html', form=form)

@app.route('/change-admin-panel-password', methods=['GET', 'POST'])
@login_required
@admin_panel_required
def change_admin_panel_password():
    form = ChangeAdminPanelPasswordForm()
    if form.validate_on_submit():
        if not check_password_hash(current_user.admin_panel_password_hash, form.current_password.data):
            flash('Current admin panel password is incorrect.', 'danger')
            return render_template('change_admin_panel_password.html', form=form)
        current_user.admin_panel_password_hash = generate_password_hash(form.new_password.data)
        from extensions import db
        db.session.commit()
        session.pop('admin_panel_authenticated', None)
        flash('Admin panel password changed. Please log in again with the new password.', 'success')
        return redirect(url_for('admin_panel_password'))
    return render_template('change_admin_panel_password.html', form=form)

@app.route('/reset-admin-panel-password', methods=['GET', 'POST'])
@login_required
def reset_admin_panel_password():
    form = ResetAdminPanelPasswordForm()
    if form.validate_on_submit():
        if not check_password_hash(current_user.password, form.main_account_password.data):
            flash('Main account password is incorrect.', 'danger')
            return render_template('reset_admin_panel_password.html', form=form)
        current_user.admin_panel_password_hash = generate_password_hash(form.new_password.data)
        from extensions import db
        db.session.commit()
        session.pop('admin_panel_authenticated', None)
        flash('Admin panel password reset. Please log in again with the new password.', 'success')
        return redirect(url_for('admin_panel_password'))
    return render_template('reset_admin_panel_password.html', form=form)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Commission System Routes

@app.route('/commission-dashboard')
@login_required
@admin_panel_required
def commission_dashboard():
    """Restaurant owner commission dashboard"""
    try:
        # Get commission summary for current restaurant
        summary = CommissionService.get_restaurant_commission_summary(current_user.id)
        
        # Get pending bills
        pending_bills = CommissionService.get_pending_commission_bills(current_user.id)
        
        # Get recent commission transactions
        recent_transactions = CommissionTransaction.query.filter_by(
            restaurant_id=current_user.id
        ).order_by(CommissionTransaction.created_at.desc()).limit(10).all()
        
        # Get platform settings for payment instructions
        platform_settings = PlatformSettings.query.first()
        
        return render_template('commission_dashboard.html', 
            summary=summary,
            pending_bills=pending_bills,
            recent_transactions=recent_transactions,
            platform_settings=platform_settings
        )
    except Exception as e:
        app.logger.error(f"Error in commission dashboard: {str(e)}")
        flash('Error loading commission dashboard', 'error')
        return redirect(url_for('dashboard'))

@app.route('/admin/commission-settings', methods=['GET', 'POST'])
@login_required
@admin_panel_required
def commission_settings():
    """Admin interface to configure commission rates"""
    if not current_user.is_admin:
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('admin_dashboard'))
    try:
        # Get all restaurants (non-admin users with restaurant_name)
        restaurants = db.session.execute(
            db.select(User).where(
                User.is_admin == False,
                User.restaurant_name != 'System Administrator'
            ).order_by(User.restaurant_name)
        ).scalars().all()
        
        if request.method == 'POST':
            restaurant_id = request.form.get('restaurant_id', type=int)
            commission_type = request.form.get('commission_type', 'percentage')
            commission_rate = request.form.get('commission_rate', type=float)
            minimum_order_amount = request.form.get('minimum_order_amount', type=float) or 0.0
            maximum_commission_raw = request.form.get('maximum_commission', type=float)
            maximum_commission = maximum_commission_raw if (maximum_commission_raw is not None and maximum_commission_raw > 0) else None
            
            if not restaurant_id:
                flash('Please select a restaurant.', 'error')
            elif commission_rate is None or commission_rate < 0:
                flash('Please enter a valid commission rate.', 'error')
            elif commission_type == 'percentage' and commission_rate > 100:
                flash('Percentage cannot exceed 100%.', 'error')
            else:
                success = CommissionService.update_commission_config(
                    restaurant_id, commission_type, commission_rate,
                    minimum_order_amount, maximum_commission
                )
                
                if success:
                    flash('Commission configuration updated successfully!', 'success')
                else:
                    flash('Error updating commission configuration', 'error')
                
                return redirect(url_for('commission_settings'))
        
        # Get current commission configs (display only, do not create)
        commission_configs = {}
        configs_for_js = {}
        for restaurant in restaurants:
            config = CommissionService.get_commission_config_for_display(restaurant.id)
            commission_configs[restaurant.id] = config
            if config:
                configs_for_js[restaurant.id] = {
                    'commission_type': config.commission_type,
                    'commission_rate': config.commission_rate,
                    'minimum_order_amount': config.minimum_order_amount or 0,
                    'maximum_commission': config.maximum_commission
                }
        
        return render_template('admin/commission_settings.html', 
            restaurants=restaurants,
            commission_configs=commission_configs,
            configs_for_js=configs_for_js
        )
    except Exception as e:
        app.logger.error(f"Error in commission settings: {str(e)}")
        flash('Error loading commission settings', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/commission-reports')
@login_required
def commission_reports():
    """Commission reports and analytics"""
    try:
        # Get date range from query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        start_date = None
        end_date = None
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        
        # Get platform commission summary
        platform_summary = CommissionService.get_platform_commission_summary(start_date, end_date)
        
        # Get restaurant-wise breakdown
        restaurants = User.query.filter_by(is_admin=False).all()
        restaurant_commissions = {}
        
        for restaurant in restaurants:
            summary = CommissionService.get_restaurant_commission_summary(
                restaurant.id, start_date, end_date
            )
            if summary:
                restaurant_commissions[restaurant.id] = {
                    'restaurant': restaurant,
                    'summary': summary
                }
        
        return render_template('admin/commission_reports.html', 
            platform_summary=platform_summary,
            restaurant_commissions=restaurant_commissions,
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        app.logger.error(f"Error in commission reports: {str(e)}")
        flash('Error loading commission reports', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/smart-kitchen')
@login_required
def smart_kitchen():
    try:
        display_statuses = ['preparing', 'ready']
        dine_in_orders = db.session.query(Order).filter(
            Order.restaurant_id == current_user.id,
            Order.status.in_(display_statuses),
            Order.order_type == 'dine_in',
            Order.status != 'archived'
        ).order_by(Order.created_at.desc()).all()

        delivery_orders = db.session.query(Order).filter(
            Order.restaurant_id == current_user.id,
            Order.status.in_(display_statuses),
            Order.order_type == 'delivery',
            Order.status != 'archived'
        ).order_by(Order.created_at.desc()).all()

        return render_template(
            'smart_kitchen.html',
            dine_in_orders=dine_in_orders,
            delivery_orders=delivery_orders,
            user_currency=current_user.currency
        )
    except Exception as e:
        app.logger.error(f"Error loading Smart Kitchen: {str(e)}")
        flash('Error loading Smart Kitchen view', 'danger')
        return redirect(url_for('view_orders'))

@app.route('/admin/commission-bills')
@login_required
def commission_bills():
    """Manage commission bills"""
    try:
        # Get all pending bills
        pending_bills = CommissionService.get_pending_commission_bills()
        
        # Get overdue bills
        overdue_bills = CommissionBill.query.filter_by(status='overdue').all()
        
        # Get paid bills (recent)
        paid_bills = CommissionBill.query.filter_by(status='paid').order_by(
            CommissionBill.paid_date.desc()
        ).limit(20).all()
        
        from datetime import datetime as _dt
        now = _dt.now()
        return render_template('admin/commission_bills.html', 
            pending_bills=pending_bills,
            overdue_bills=overdue_bills,
            paid_bills=paid_bills,
            now=now
        )
    except Exception as e:
        app.logger.error(f"Error in commission bills: {str(e)}")
        flash('Error loading commission bills', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/confirm-commission-payment/<int:bill_id>', methods=['POST'])
@login_required
def confirm_commission_payment(bill_id):
    """Admin confirms commission payment received"""
    try:
        if not current_user.is_admin:
            flash('Unauthorized', 'error')
            return redirect(url_for('commission_bills'))
        payment_reference = request.form.get('payment_reference')
        amount_received = request.form.get('amount_received', type=float)
        
        if not payment_reference or amount_received is None:
            flash('Payment reference and amount are required', 'error')
            return redirect(url_for('commission_bills'))
        
        success, message = CommissionService.confirm_commission_payment(
            bill_id, payment_reference, amount_received, confirmer_user_id=current_user.id
        )
        
        if success:
            flash('Commission payment confirmed successfully!', 'success')
        else:
            flash(f'Error confirming payment: {message}', 'error')
        
        return redirect(url_for('commission_bills'))
    except Exception as e:
        app.logger.error(f"Error confirming commission payment: {str(e)}")
        flash('Error confirming payment', 'error')
        return redirect(url_for('commission_bills'))

@app.route('/admin/generate-commission-bill/<int:restaurant_id>')
@login_required
def generate_commission_bill(restaurant_id):
    """Generate commission bill for a restaurant"""
    try:
        # Get current month
        now = datetime.now(UTC)
        year = now.year
        month = now.month
        
        # Generate bill for previous month
        if month == 1:
            year -= 1
            month = 12
        else:
            month -= 1
        
        bill = CommissionService.generate_monthly_commission_bill(restaurant_id, year, month)
        
        if bill:
            flash(f'Commission bill generated for {year}-{month:02d}', 'success')
        else:
            flash('No commission transactions found for this period', 'info')
        
        return redirect(url_for('commission_bills'))
    except Exception as e:
        app.logger.error(f"Error generating commission bill: {str(e)}")
        flash('Error generating commission bill', 'error')
        return redirect(url_for('commission_bills'))

@app.route('/admin/generate-commission-bills-all')
@login_required
def generate_commission_bills_all():
    """Generate commission bills for all restaurants for the previous month"""
    try:
        if not current_user.is_admin:
            flash('Unauthorized', 'error')
            return redirect(url_for('commission_bills'))
        # Optional query params: year, month
        year_param = request.args.get('year', type=int)
        month_param = request.args.get('month', type=int)
        if year_param and month_param:
            year = year_param
            month = month_param
        else:
            # Determine previous month
            now = datetime.now(UTC)
            year = now.year
            month = now.month
            if month == 1:
                year -= 1
                month = 12
            else:
                month -= 1
        restaurants = User.query.filter_by(is_admin=False).all()
        generated = 0
        skipped = 0
        for r in restaurants:
            bill = CommissionService.generate_monthly_commission_bill(r.id, year, month)
            if bill:
                generated += 1
            else:
                skipped += 1
        if generated:
            flash(f'Generated {generated} bill(s). Skipped {skipped} with no transactions.', 'success')
        else:
            flash('No bills generated. No commission transactions found for last month.', 'info')
        return redirect(url_for('commission_bills'))
    except Exception as e:
        app.logger.error(f"Error generating commission bills: {str(e)}")
        flash('Error generating commission bills', 'error')
        return redirect(url_for('commission_bills'))

@app.route('/admin/generate-commission-bill-range')
@login_required
def generate_commission_bill_range():
    """Generate commission bills for a given year+month for a specific restaurant or all."""
    try:
        if not current_user.is_admin:
            flash('Unauthorized', 'error')
            return redirect(url_for('commission_bills'))
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        restaurant_id = request.args.get('restaurant_id', type=int)
        if not year or not month or month < 1 or month > 12:
            flash('Provide valid year and month.', 'error')
            return redirect(url_for('commission_bills'))
        targets = []
        if restaurant_id:
            targets = [User.query.get(restaurant_id)] if User.query.get(restaurant_id) else []
        else:
            targets = User.query.filter_by(is_admin=False).all()
        if not targets:
            flash('No target restaurants found.', 'info')
            return redirect(url_for('commission_bills'))
        generated = 0
        skipped = 0
        for r in targets:
            bill = CommissionService.generate_monthly_commission_bill(r.id, year, month)
            if bill:
                generated += 1
            else:
                skipped += 1
        flash(f'Generated {generated} bill(s). Skipped {skipped}.', 'success' if generated else 'info')
        return redirect(url_for('commission_bills'))
    except Exception as e:
        app.logger.error(f"Error generating commission bills by range: {str(e)}")
        flash('Error generating commission bills', 'error')
        return redirect(url_for('commission_bills'))

@app.route('/admin/generate-commission-bill-by-id')
@login_required
def generate_commission_bill_by_id():
    """Generate a commission bill for a single restaurant. Month/year optional (defaults to previous month)."""
    try:
        if not current_user.is_admin:
            flash('Unauthorized', 'error')
            return redirect(url_for('commission_bills'))
        restaurant_id = request.args.get('restaurant_id', type=int)
        if not restaurant_id:
            flash('Provide a valid restaurant ID.', 'error')
            return redirect(url_for('commission_bills'))
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        if not (year and month):
            now = datetime.now(UTC)
            year = now.year
            month = now.month
            if month == 1:
                year -= 1
                month = 12
            else:
                month -= 1
        bill = CommissionService.generate_monthly_commission_bill(restaurant_id, year, month)
        if bill:
            flash(f'Generated bill for restaurant {restaurant_id} - {year}-{month:02d}.', 'success')
        else:
            flash('No commission transactions found for that period.', 'info')
        return redirect(url_for('commission_bills'))
    except Exception as e:
        app.logger.error(f"Error generating commission bill by id: {str(e)}")
        flash('Error generating commission bill', 'error')
        return redirect(url_for('commission_bills'))

@app.route('/admin/commission-bill/<int:bill_id>')
@login_required
def view_commission_bill(bill_id):
    """View commission bill details"""
    try:
        bill = CommissionBill.query.get_or_404(bill_id)
        restaurant = User.query.get(bill.restaurant_id)
        
        # Get commission transactions for this bill
        transactions = CommissionTransaction.query.filter(
            and_(
                CommissionTransaction.restaurant_id == bill.restaurant_id,
                CommissionTransaction.created_at >= bill.period_start,
                CommissionTransaction.created_at <= bill.period_end
            )
        ).all()
        
        from datetime import datetime as _dt
        now = _dt.now()
        return render_template('admin/commission_bill_detail.html', 
            bill=bill,
            restaurant=restaurant,
            transactions=transactions,
            now=now
        )
    except Exception as e:
        app.logger.error(f"Error viewing commission bill: {str(e)}")
        flash('Error loading commission bill', 'error')
        return redirect(url_for('commission_bills'))

# Notification System API Endpoints
@app.route('/api/notifications')
@login_required
def get_notifications():
    """Get notifications for the current user."""
    try:
        from models import Notification, NotificationRead
        from sqlalchemy.exc import ProgrammingError, OperationalError
        
        # Check if notification table exists
        try:
            # Try to query the table - if it doesn't exist, this will raise an error
            db.session.query(Notification).limit(1).all()
        except (ProgrammingError, OperationalError) as e:
            # Table doesn't exist, return empty notifications
            if 'does not exist' in str(e) or 'relation' in str(e).lower():
                app.logger.warning("Notification table does not exist. Returning empty notifications.")
                return jsonify({
                    'success': True,
                    'notifications': [],
                    'unread_count': 0
                })
            else:
                raise
        
        # Get notifications for this user (global or targeted to this restaurant)
        notifications_query = db.session.query(Notification).filter(
            db.or_(
                Notification.is_global == True,
                Notification.target_restaurant_id == current_user.id
            ),
            Notification.is_active == True,
            db.or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > datetime.now(UTC)
            )
        ).order_by(Notification.created_at.desc())
        
        notifications = notifications_query.all()
        
        # Get read status for each notification
        notification_data = []
        for notification in notifications:
            is_read = db.session.query(NotificationRead).filter(
                NotificationRead.notification_id == notification.id,
                NotificationRead.user_id == current_user.id
            ).first() is not None
            
            notification_data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.notification_type,
                'priority': notification.priority,
                'created_at': notification.created_at.isoformat(),
                'is_read': is_read
            })
        
        return jsonify({
            'success': True,
            'notifications': notification_data,
            'unread_count': len([n for n in notification_data if not n['is_read']])
        })
        
    except Exception as e:
        app.logger.error(f"Error getting notifications: {str(e)}")
        # Return empty notifications instead of error to prevent frontend crashes
        return jsonify({
            'success': True,
            'notifications': [],
            'unread_count': 0
        })

@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read."""
    try:
        from models import Notification, NotificationRead
        from sqlalchemy.exc import ProgrammingError, OperationalError
        
        # Check if notification table exists
        try:
            db.session.query(Notification).limit(1).all()
        except (ProgrammingError, OperationalError) as e:
            if 'does not exist' in str(e) or 'relation' in str(e).lower():
                return jsonify({'success': False, 'message': 'Notification system not initialized'}), 503
            else:
                raise
        
        # Check if notification exists and is accessible to user
        notification = db.session.query(Notification).filter(
            Notification.id == notification_id,
            db.or_(
                Notification.is_global == True,
                Notification.target_restaurant_id == current_user.id
            )
        ).first()
        
        if not notification:
            return jsonify({'success': False, 'message': 'Notification not found'}), 404
        
        # Check if already read
        existing_read = db.session.query(NotificationRead).filter(
            NotificationRead.notification_id == notification_id,
            NotificationRead.user_id == current_user.id
        ).first()
        
        if not existing_read:
            # Mark as read
            read_record = NotificationRead(
                notification_id=notification_id,
                user_id=current_user.id
            )
            db.session.add(read_record)
            db.session.commit()
        
        return jsonify({'success': True, 'message': 'Notification marked as read'})
        
    except Exception as e:
        app.logger.error(f"Error marking notification as read: {str(e)}")
        return jsonify({'success': False, 'message': 'Error marking notification as read'}), 500

@app.route('/api/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read for the current user."""
    try:
        from models import Notification, NotificationRead
        from sqlalchemy.exc import ProgrammingError, OperationalError
        
        # Check if notification table exists
        try:
            db.session.query(Notification).limit(1).all()
        except (ProgrammingError, OperationalError) as e:
            if 'does not exist' in str(e) or 'relation' in str(e).lower():
                return jsonify({'success': False, 'message': 'Notification system not initialized'}), 503
            else:
                raise
        
        # Get all unread notifications for this user
        notifications_query = db.session.query(Notification).filter(
            db.or_(
                Notification.is_global == True,
                Notification.target_restaurant_id == current_user.id
            ),
            Notification.is_active == True,
            db.or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > datetime.now(UTC)
            )
        )
        
        notifications = notifications_query.all()
        
        # Mark each as read if not already read
        for notification in notifications:
            existing_read = db.session.query(NotificationRead).filter(
                NotificationRead.notification_id == notification.id,
                NotificationRead.user_id == current_user.id
            ).first()
            
            if not existing_read:
                read_record = NotificationRead(
                    notification_id=notification.id,
                    user_id=current_user.id
                )
                db.session.add(read_record)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'All notifications marked as read'})
        
    except Exception as e:
        app.logger.error(f"Error marking all notifications as read: {str(e)}")
        return jsonify({'success': False, 'message': 'Error marking notifications as read'}), 500

@app.route('/admin/notifications')
@login_required
def admin_notifications():
    """Admin panel for managing notifications."""
    if not current_user.is_admin:
        flash('Unauthorized', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        from models import Notification, User
        
        # Get all notifications
        notifications = db.session.query(Notification).order_by(Notification.created_at.desc()).all()
        
        # Get all restaurants for targeting
        restaurants = db.session.query(User).filter(User.is_admin == False).all()
        
        return render_template('admin/notifications.html', 
                             notifications=notifications, 
                             restaurants=restaurants,
                             csrf_token=generate_csrf())
        
    except Exception as e:
        app.logger.error(f"Error loading admin notifications: {str(e)}")
        flash('Error loading notifications', 'error')
        return redirect(url_for('admin_panel'))

@app.route('/admin/notifications/create', methods=['GET', 'POST'])
@login_required
def create_notification():
    """Create a new notification."""
    if not current_user.is_admin:
        flash('Unauthorized', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            from models import Notification
            
            title = request.form.get('title', '').strip()
            message = request.form.get('message', '').strip()
            notification_type = request.form.get('type', 'info')
            priority = request.form.get('priority', 'normal')
            is_global = request.form.get('is_global') == 'on'
            target_restaurant_id = request.form.get('target_restaurant_id', type=int)
            expires_in_days = request.form.get('expires_in_days', type=int)
            
            if not title or not message:
                flash('Title and message are required', 'error')
                return redirect(url_for('create_notification'))
            
            # Calculate expiration date if provided
            expires_at = None
            if expires_in_days and expires_in_days > 0:
                expires_at = datetime.now(UTC) + timedelta(days=expires_in_days)
            
            # Create notification
            notification = Notification(
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority,
                is_global=is_global,
                target_restaurant_id=target_restaurant_id if not is_global else None,
                created_by=current_user.id,
                expires_at=expires_at
            )
            
            db.session.add(notification)
            db.session.commit()
            
            flash('Notification created successfully', 'success')
            return redirect(url_for('admin_notifications'))
            
        except Exception as e:
            app.logger.error(f"Error creating notification: {str(e)}")
            flash('Error creating notification', 'error')
            return redirect(url_for('create_notification'))
    
    # GET request - show form
    try:
        from models import User
        restaurants = db.session.query(User).filter(User.is_admin == False).all()
        return render_template('admin/create_notification.html', 
                             restaurants=restaurants,
                             csrf_token=generate_csrf())
    except Exception as e:
        app.logger.error(f"Error loading create notification form: {str(e)}")
        flash('Error loading form', 'error')
        return redirect(url_for('admin_notifications'))

@app.route('/admin/notifications/<int:notification_id>/toggle', methods=['POST'])
@login_required
def toggle_notification(notification_id):
    """Toggle notification active status."""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        from models import Notification
        
        notification = db.session.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            return jsonify({'success': False, 'message': 'Notification not found'}), 404
        
        notification.is_active = not notification.is_active
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'is_active': notification.is_active,
            'message': f'Notification {"activated" if notification.is_active else "deactivated"}'
        })
        
    except Exception as e:
        app.logger.error(f"Error toggling notification: {str(e)}")
        return jsonify({'success': False, 'message': 'Error updating notification'}), 500

@app.route('/admin/notifications/<int:notification_id>/delete', methods=['POST'])
@login_required
def delete_notification(notification_id):
    """Delete a notification."""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        from models import Notification, NotificationRead
        
        # Delete read records first
        db.session.query(NotificationRead).filter(
            NotificationRead.notification_id == notification_id
        ).delete()
        
        # Delete notification
        notification = db.session.query(Notification).filter(Notification.id == notification_id).first()
        if notification:
            db.session.delete(notification)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Notification deleted'})
        else:
            return jsonify({'success': False, 'message': 'Notification not found'}), 404
        
    except Exception as e:
        app.logger.error(f"Error deleting notification: {str(e)}")
        return jsonify({'success': False, 'message': 'Error deleting notification'}), 500

# Replace app.run with socketio.run
if __name__ == "__main__":
    if async_mode == "gevent":
        from gevent import monkey
        monkey.patch_all()
    elif async_mode == "eventlet":
        import eventlet
        eventlet.monkey_patch()
    print("SocketIO async_mode is", socketio.async_mode)
    try:
        print("Starting BlueSpace Restaurant server...")
        print("Press Ctrl+C to stop the server")
        socketio.run(app, host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\nShutdown signal received, cleaning up...")
        cleanup_on_shutdown()
        print("Server stopped gracefully")
    except Exception as e:
        print(f"Error starting server: {e}")
        cleanup_on_shutdown()
        sys.exit(1)