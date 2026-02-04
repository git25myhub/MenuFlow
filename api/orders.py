"""
Orders API endpoints
"""
from flask import request, jsonify
from api import api_bp
from api.auth import require_auth
from models import Order, OrderItem, MenuItem
from extensions import db
from datetime import datetime
from sqlalchemy import desc


@api_bp.route('/orders', methods=['GET'])
@require_auth
def get_orders():
    """Get orders for authenticated user's restaurant"""
    user = request.current_user
    status = request.args.get('status')
    limit = request.args.get('limit', type=int, default=50)
    offset = request.args.get('offset', type=int, default=0)
    
    query = Order.query.filter_by(restaurant_id=user.restaurant_id)
    
    if status:
        query = query.filter_by(status=status)
    
    orders = query.order_by(desc(Order.created_at)).limit(limit).offset(offset).all()
    
    return jsonify({
        'success': True,
        'orders': [order_to_dict(order) for order in orders],
        'count': len(orders)
    }), 200


@api_bp.route('/orders/<int:order_id>/track', methods=['GET'])
def track_order(order_id):
    """Get order status (public - for customer order tracking)"""
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    return jsonify({
        'success': True,
        'order': {
            'id': order.id,
            'status': order.status,
            'total': float(order.total_amount) if order.total_amount else 0,
            'created_at': order.created_at.isoformat() if order.created_at else None,
        }
    }), 200


@api_bp.route('/orders/<int:order_id>', methods=['GET'])
@require_auth
def get_order(order_id):
    """Get specific order details"""
    user = request.current_user
    order = Order.query.filter_by(id=order_id, restaurant_id=user.restaurant_id).first()
    
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    return jsonify({
        'success': True,
        'order': order_to_dict(order, include_items=True)
    }), 200


@api_bp.route('/orders/guest', methods=['POST'])
def create_guest_order():
    """Create order as guest (no auth - for customer app)"""
    from models import User
    data = request.get_json()
    
    required_fields = ['items', 'order_type', 'total', 'restaurant_id']
    for field in required_fields:
        if data.get(field) is None:
            return jsonify({'error': f'{field} is required'}), 400
    
    restaurant_id = data['restaurant_id']
    user = User.query.filter_by(restaurant_id=restaurant_id).first()
    if not user:
        user = User.query.filter_by(id=restaurant_id).first()
    if not user:
        return jsonify({'error': 'Restaurant not found'}), 404
    
    order = Order(
        restaurant_id=user.restaurant_id or user.id,
        user_id=user.id,
        order_type=data['order_type'],
        total_amount=data['total'],
        status='new',
        special_instructions=data.get('special_instructions'),
        delivery_address=data.get('delivery_address'),
        customer_name=data.get('customer_name'),
        customer_phone=data.get('customer_phone')
    )
    
    db.session.add(order)
    db.session.flush()
    
    for item_data in data['items']:
        menu_item = MenuItem.query.get(item_data['menu_item_id'])
        if not menu_item:
            db.session.rollback()
            return jsonify({'error': f"Menu item {item_data['menu_item_id']} not found"}), 404
        
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=item_data['menu_item_id'],
            quantity=item_data['quantity'],
            price=menu_item.price,
            name=menu_item.name
        )
        db.session.add(order_item)
        
        if menu_item.stock is not None:
            menu_item.stock -= item_data['quantity']
            if menu_item.stock < 0:
                menu_item.stock = 0
    
    db.session.commit()
    
    result = {
        'id': order.id,
        'restaurant_id': order.restaurant_id,
        'order_type': order.order_type,
        'total': float(order.total_amount),
        'status': order.status,
        'created_at': order.created_at.isoformat() if order.created_at else None,
        'items': [{
            'id': oi.id,
            'menu_item_id': oi.menu_item_id,
            'item_name': oi.name,
            'quantity': oi.quantity,
            'price': float(oi.price) if oi.price else 0.0
        } for oi in order.order_items]
    }
    return jsonify({'success': True, 'order': result}), 201


@api_bp.route('/orders', methods=['POST'])
@require_auth
def create_order():
    """Create a new order (authenticated)"""
    user = request.current_user
    data = request.get_json()
    
    required_fields = ['items', 'order_type', 'total']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Create order
    order = Order(
        restaurant_id=user.restaurant_id,
        user_id=user.id,
        order_type=data['order_type'],
        total=data['total'],
        status='new',
        special_instructions=data.get('special_instructions'),
        delivery_address=data.get('delivery_address'),
        customer_name=data.get('customer_name'),
        customer_phone=data.get('customer_phone')
    )
    
    db.session.add(order)
    db.session.flush()
    
    # Create order items
    for item_data in data['items']:
        menu_item = MenuItem.query.get(item_data['menu_item_id'])
        if not menu_item:
            db.session.rollback()
            return jsonify({'error': f"Menu item {item_data['menu_item_id']} not found"}), 404
        
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=item_data['menu_item_id'],
            quantity=item_data['quantity'],
            price=menu_item.price,
            item_name=menu_item.name
        )
        db.session.add(order_item)
        
        # Update stock if applicable
        if menu_item.stock is not None:
            menu_item.stock -= item_data['quantity']
            if menu_item.stock < 0:
                menu_item.stock = 0
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'order': order_to_dict(order, include_items=True)
    }), 201


@api_bp.route('/orders/<int:order_id>/status', methods=['PUT'])
@require_auth
def update_order_status(order_id):
    """Update order status"""
    user = request.current_user
    data = request.get_json()
    new_status = data.get('status')
    
    if not new_status:
        return jsonify({'error': 'Status is required'}), 400
    
    order = Order.query.filter_by(id=order_id, restaurant_id=user.restaurant_id).first()
    
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    # Validate status transition
    valid_statuses = ['new', 'pending', 'paid', 'preparing', 'ready', 'delivered', 'cancelled']
    if new_status not in valid_statuses:
        return jsonify({'error': 'Invalid status'}), 400
    
    order.status = new_status
    order.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'order': order_to_dict(order)
    }), 200


@api_bp.route('/orders/<int:order_id>', methods=['DELETE'])
@require_auth
def cancel_order(order_id):
    """Cancel an order"""
    user = request.current_user
    order = Order.query.filter_by(id=order_id, restaurant_id=user.restaurant_id).first()
    
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    # Restore stock
    for item in order.items:
        menu_item = MenuItem.query.get(item.menu_item_id)
        if menu_item and menu_item.stock is not None:
            menu_item.stock += item.quantity
    
    order.status = 'cancelled'
    order.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Order cancelled successfully'
    }), 200


def order_to_dict(order, include_items=False):
    """Convert Order model to dictionary"""
    result = {
        'id': order.id,
        'restaurant_id': order.restaurant_id,
        'order_type': order.order_type,
        'total': float(order.total) if order.total else 0.0,
        'status': order.status,
        'special_instructions': order.special_instructions,
        'delivery_address': order.delivery_address,
        'customer_name': order.customer_name,
        'customer_phone': order.customer_phone,
        'created_at': order.created_at.isoformat() if order.created_at else None,
        'updated_at': order.updated_at.isoformat() if order.updated_at else None
    }
    
    if include_items:
        result['items'] = [{
            'id': item.id,
            'menu_item_id': item.menu_item_id,
            'item_name': item.item_name,
            'quantity': item.quantity,
            'price': float(item.price) if item.price else 0.0
        } for item in order.items]
    
    return result

