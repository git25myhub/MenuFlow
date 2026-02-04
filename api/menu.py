"""
Menu API endpoints
"""
from flask import request, jsonify
from api import api_bp
from api.auth import require_auth
from models import MenuItem, Category
from extensions import db
from werkzeug.utils import secure_filename
import os
from PIL import Image


@api_bp.route('/menu/items', methods=['GET'])
def get_menu_items():
    """Get menu items (public endpoint)"""
    restaurant_id = request.args.get('restaurant_id', type=int)
    category_id = request.args.get('category_id', type=int)
    
    if not restaurant_id:
        return jsonify({'error': 'restaurant_id is required'}), 400
    
    # MenuItem uses user_id (restaurant owner); restaurant_id maps to user_id in this schema
    query = MenuItem.query.filter_by(user_id=restaurant_id)
    if hasattr(MenuItem, 'is_available'):
        query = query.filter_by(is_available=True)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    items = query.order_by(MenuItem.name).all()
    
    return jsonify({
        'success': True,
        'items': [menu_item_to_dict(item) for item in items]
    }), 200


@api_bp.route('/menu/items/<int:item_id>', methods=['GET'])
def get_menu_item(item_id):
    """Get specific menu item (public endpoint)"""
    item = MenuItem.query.get(item_id)
    
    if not item:
        return jsonify({'error': 'Menu item not found'}), 404
    
    return jsonify({
        'success': True,
        'item': menu_item_to_dict(item)
    }), 200


@api_bp.route('/menu/items', methods=['POST'])
@require_auth
def create_menu_item():
    """Create a new menu item"""
    user = request.current_user
    
    data = request.get_json()
    required_fields = ['name', 'price', 'category_id']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Verify category belongs to restaurant
    category = Category.query.filter_by(
        id=data['category_id'],
        restaurant_id=user.restaurant_id
    ).first()
    
    if not category:
        return jsonify({'error': 'Category not found'}), 404
    
    item = MenuItem(
        restaurant_id=user.restaurant_id,
        name=data['name'],
        description=data.get('description'),
        price=data['price'],
        category_id=data['category_id'],
        image_url=data.get('image_url'),
        is_available=data.get('is_available', True),
        stock=data.get('stock')
    )
    
    db.session.add(item)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'item': menu_item_to_dict(item)
    }), 201


@api_bp.route('/menu/items/<int:item_id>', methods=['PUT'])
@require_auth
def update_menu_item(item_id):
    """Update a menu item"""
    user = request.current_user
    item = MenuItem.query.filter_by(id=item_id, restaurant_id=user.restaurant_id).first()
    
    if not item:
        return jsonify({'error': 'Menu item not found'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        item.name = data['name']
    if 'description' in data:
        item.description = data['description']
    if 'price' in data:
        item.price = data['price']
    if 'category_id' in data:
        item.category_id = data['category_id']
    if 'image_url' in data:
        item.image_url = data['image_url']
    if 'is_available' in data:
        item.is_available = data['is_available']
    if 'stock' in data:
        item.stock = data['stock']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'item': menu_item_to_dict(item)
    }), 200


@api_bp.route('/menu/items/<int:item_id>', methods=['DELETE'])
@require_auth
def delete_menu_item(item_id):
    """Delete a menu item"""
    user = request.current_user
    item = MenuItem.query.filter_by(id=item_id, restaurant_id=user.restaurant_id).first()
    
    if not item:
        return jsonify({'error': 'Menu item not found'}), 404
    
    db.session.delete(item)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Menu item deleted successfully'
    }), 200


@api_bp.route('/menu/categories', methods=['GET'])
def get_categories():
    """Get categories (public endpoint)"""
    restaurant_id = request.args.get('restaurant_id', type=int)
    
    if not restaurant_id:
        return jsonify({'error': 'restaurant_id is required'}), 400
    
    if hasattr(Category, 'restaurant_id'):
        categories = Category.query.filter_by(restaurant_id=restaurant_id).order_by(Category.name).all()
    else:
        categories = Category.query.order_by(Category.name).all()
    
    return jsonify({
        'success': True,
        'categories': [category_to_dict(cat) for cat in categories]
    }), 200


def menu_item_to_dict(item):
    """Convert MenuItem model to dictionary"""
    return {
        'id': item.id,
        'restaurant_id': getattr(item, 'restaurant_id', item.user_id),
        'name': item.name,
        'description': item.description,
        'price': float(item.price) if item.price else 0.0,
        'category_id': item.category_id,
        'image_url': item.image_url,
        'is_available': getattr(item, 'is_available', True),
        'stock': getattr(item, 'stock', 0)
    }


def category_to_dict(category):
    """Convert Category model to dictionary"""
    return {
        'id': category.id,
        'restaurant_id': getattr(category, 'restaurant_id', None),
        'name': category.name,
        'description': category.description
    }

