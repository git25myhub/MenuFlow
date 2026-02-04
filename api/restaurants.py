"""
Restaurants API endpoints
"""
from flask import request, jsonify
from api import api_bp
from api.auth import require_auth
from models import User, Restaurant
from extensions import db


@api_bp.route('/restaurants', methods=['GET'])
def list_restaurants():
    """List all restaurants (public - for customer app)"""
    restaurants = User.query.filter(
        User.restaurant_id.isnot(None),
        User.restaurant_name != 'System Administrator'
    ).all()
    
    # Deduplicate by restaurant_id
    seen = set()
    result = []
    for user in restaurants:
        rid = user.restaurant_id or user.id
        if rid not in seen:
            seen.add(rid)
            result.append({
                'id': rid,
                'name': user.restaurant_name,
                'logo_url': user.logo_url,
                'description': user.restaurant_description,
                'currency': user.currency or 'USD',
            })
    
    return jsonify({
        'success': True,
        'restaurants': result
    }), 200


@api_bp.route('/restaurants/me', methods=['GET'])
@require_auth
def get_my_restaurant():
    """Get authenticated user's restaurant info"""
    user = request.current_user
    
    return jsonify({
        'success': True,
        'restaurant': {
            'id': user.restaurant_id or user.id,
            'name': user.restaurant_name,
            'logo_url': user.logo_url,
            'currency': user.currency,
            'description': user.restaurant_description,
            'address': user.restaurant_address,
            'contact_phone': user.contact_phone,
            'theme_color': user.theme_color,
            'payment_method': user.payment_method
        }
    }), 200


@api_bp.route('/restaurants/me', methods=['PUT'])
@require_auth
def update_my_restaurant():
    """Update authenticated user's restaurant info"""
    user = request.current_user
    data = request.get_json()
    
    # Update allowed fields
    allowed_fields = [
        'restaurant_name', 'logo_url', 'currency', 'restaurant_description',
        'restaurant_address', 'contact_phone', 'theme_color', 'payment_method',
        'mpesa_number', 'opening_hours', 'website'
    ]
    
    for field in allowed_fields:
        if field in data:
            setattr(user, field, data[field])
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'restaurant': {
            'id': user.restaurant_id or user.id,
            'name': user.restaurant_name,
            'logo_url': user.logo_url,
            'currency': user.currency
        }
    }), 200


@api_bp.route('/restaurants/<int:restaurant_id>', methods=['GET'])
def get_restaurant(restaurant_id):
    """Get public restaurant info (for customer app)"""
    user = User.query.filter_by(restaurant_id=restaurant_id).first()
    
    if not user:
        return jsonify({'error': 'Restaurant not found'}), 404
    
    return jsonify({
        'success': True,
        'restaurant': {
            'id': user.restaurant_id or user.id,
            'name': user.restaurant_name,
            'logo_url': user.logo_url,
            'currency': user.currency,
            'description': user.restaurant_description,
            'address': user.restaurant_address,
            'contact_phone': user.contact_phone,
            'theme_color': user.theme_color,
            'opening_hours': user.opening_hours
        }
    }), 200

