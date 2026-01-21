"""
Authentication API endpoints
"""
from flask import request, jsonify
from flask_login import login_user, logout_user, current_user
from api import api_bp
from models import User
from extensions import db
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import jwt
import os

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', os.environ.get('SECRET_KEY', 'dev-secret-key'))
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION = 86400  # 24 hours


def generate_token(user):
    """Generate JWT token for user"""
    payload = {
        'user_id': user.id,
        'email': user.email,
        'restaurant_id': user.restaurant_id,
        'is_admin': user.is_admin,
        'exp': datetime.utcnow().timestamp() + JWT_EXPIRATION
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token):
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


@api_bp.route('/auth/login', methods=['POST'])
def login():
    """Mobile app login endpoint"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Generate JWT token
    token = generate_token(user)
    
    return jsonify({
        'success': True,
        'token': token,
        'user': {
            'id': user.id,
            'email': user.email,
            'restaurant_id': user.restaurant_id,
            'restaurant_name': user.restaurant_name,
            'is_admin': user.is_admin,
            'role': user.role
        }
    }), 200


@api_bp.route('/auth/register', methods=['POST'])
def register():
    """Mobile app registration endpoint"""
    data = request.get_json()
    
    required_fields = ['email', 'password', 'restaurant_name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Check if user exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    
    # Create new user
    user = User(
        email=data['email'],
        password=generate_password_hash(data['password'], method='pbkdf2:sha256'),
        restaurant_name=data['restaurant_name'],
        currency=data.get('currency', 'USD'),
        payment_method=data.get('payment_method', 'manual')
    )
    
    db.session.add(user)
    db.session.commit()
    
    # Generate token
    token = generate_token(user)
    
    return jsonify({
        'success': True,
        'token': token,
        'user': {
            'id': user.id,
            'email': user.email,
            'restaurant_id': user.restaurant_id,
            'restaurant_name': user.restaurant_name,
            'is_admin': user.is_admin
        }
    }), 201


@api_bp.route('/auth/me', methods=['GET'])
def get_current_user():
    """Get current authenticated user"""
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Authorization token required'}), 401
    
    token = auth_header.split(' ')[1]
    payload = verify_token(token)
    
    if not payload:
        return jsonify({'error': 'Invalid or expired token'}), 401
    
    user = User.query.get(payload['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'email': user.email,
            'restaurant_id': user.restaurant_id,
            'restaurant_name': user.restaurant_name,
            'is_admin': user.is_admin,
            'role': user.role,
            'currency': user.currency
        }
    }), 200


@api_bp.route('/auth/logout', methods=['POST'])
def logout():
    """Logout endpoint (token invalidation handled client-side)"""
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200


def require_auth(f):
    """Decorator to require authentication"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401
        
        token = auth_header.split(' ')[1]
        payload = verify_token(token)
        
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        user = User.query.get(payload['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function

