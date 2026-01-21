"""
Payments API endpoints
"""
from flask import request, jsonify
from api import api_bp
from api.auth import require_auth
from models import Order
from extensions import db
from datetime import datetime


@api_bp.route('/payments/process', methods=['POST'])
@require_auth
def process_payment():
    """Process payment for an order"""
    user = request.current_user
    data = request.get_json()
    
    order_id = data.get('order_id')
    payment_method = data.get('payment_method', 'manual')
    
    if not order_id:
        return jsonify({'error': 'order_id is required'}), 400
    
    order = Order.query.filter_by(id=order_id, restaurant_id=user.restaurant_id).first()
    
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    # Update order status based on payment method
    if payment_method == 'manual':
        order.status = 'pending_confirmation'
    elif payment_method in ['mpesa', 'pesapal']:
        # Integration with payment gateways would go here
        order.status = 'pending'
        order.payment_method = payment_method
    else:
        order.status = 'paid'
        order.payment_method = payment_method
    
    order.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'order': {
            'id': order.id,
            'status': order.status,
            'payment_method': order.payment_method
        }
    }), 200


@api_bp.route('/payments/confirm/<int:order_id>', methods=['POST'])
@require_auth
def confirm_payment(order_id):
    """Confirm manual payment"""
    user = request.current_user
    order = Order.query.filter_by(id=order_id, restaurant_id=user.restaurant_id).first()
    
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    if order.status != 'pending_confirmation':
        return jsonify({'error': 'Order is not awaiting payment confirmation'}), 400
    
    order.status = 'paid'
    order.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'order': {
            'id': order.id,
            'status': order.status
        }
    }), 200


@api_bp.route('/payments/status/<int:order_id>', methods=['GET'])
@require_auth
def get_payment_status(order_id):
    """Get payment status for an order"""
    user = request.current_user
    order = Order.query.filter_by(id=order_id, restaurant_id=user.restaurant_id).first()
    
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    return jsonify({
        'success': True,
        'payment_status': order.status,
        'payment_method': order.payment_method,
        'total': float(order.total) if order.total else 0.0
    }), 200

