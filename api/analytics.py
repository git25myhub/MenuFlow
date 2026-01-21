"""
Analytics API endpoints
"""
from flask import request, jsonify, current_app
from api import api_bp
from api.auth import require_auth
from models import Order
from extensions import db
from sqlalchemy import func
from datetime import datetime, timedelta
import traceback


@api_bp.route('/analytics/dashboard', methods=['GET'])
@require_auth
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        user = request.current_user
        days = request.args.get('days', type=int, default=7)
        
        # Use user.id as restaurant_id if restaurant_id is None
        # (users can be restaurants themselves)
        restaurant_id = user.restaurant_id if user.restaurant_id is not None else user.id
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total orders
        total_orders = Order.query.filter_by(restaurant_id=restaurant_id).count()
        
        # Recent orders (last N days)
        recent_orders = Order.query.filter(
            Order.restaurant_id == restaurant_id,
            Order.created_at >= start_date
        ).count()
        
        # Total revenue
        total_revenue = db.session.query(func.sum(Order.total)).filter(
            Order.restaurant_id == restaurant_id,
            Order.status.in_(['paid', 'preparing', 'ready', 'delivered'])
        ).scalar() or 0.0
        
        # Recent revenue
        recent_revenue = db.session.query(func.sum(Order.total)).filter(
            Order.restaurant_id == restaurant_id,
            Order.created_at >= start_date,
            Order.status.in_(['paid', 'preparing', 'ready', 'delivered'])
        ).scalar() or 0.0
        
        # Orders by status
        orders_by_status = db.session.query(
            Order.status,
            func.count(Order.id)
        ).filter(
            Order.restaurant_id == restaurant_id
        ).group_by(Order.status).all()
        
        status_counts = {status: count for status, count in orders_by_status}
        
        return jsonify({
            'success': True,
            'stats': {
                'total_orders': total_orders,
                'recent_orders': recent_orders,
                'total_revenue': float(total_revenue),
                'recent_revenue': float(recent_revenue),
                'orders_by_status': status_counts,
                'currency': getattr(user, 'currency', 'USD')
            }
        }), 200
    except Exception as e:
        current_app.logger.error(f'Error in get_dashboard_stats: {str(e)}')
        current_app.logger.error(f'Traceback: {traceback.format_exc()}')
        return jsonify({
            'success': False,
            'error': f'Failed to load dashboard stats: {str(e)}'
        }), 500


@api_bp.route('/analytics/revenue', methods=['GET'])
@require_auth
def get_revenue_stats():
    """Get revenue statistics"""
    try:
        user = request.current_user
        days = request.args.get('days', type=int, default=30)
        
        # Use user.id as restaurant_id if restaurant_id is None
        # (users can be restaurants themselves)
        restaurant_id = user.restaurant_id if user.restaurant_id is not None else user.id
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Daily revenue
        daily_revenue = db.session.query(
            func.date(Order.created_at).label('date'),
            func.sum(Order.total).label('revenue')
        ).filter(
            Order.restaurant_id == restaurant_id,
            Order.created_at >= start_date,
            Order.status.in_(['paid', 'preparing', 'ready', 'delivered'])
        ).group_by(func.date(Order.created_at)).all()
        
        revenue_data = [
            {
                'date': date.isoformat(),
                'revenue': float(revenue) if revenue else 0.0
            }
            for date, revenue in daily_revenue
        ]
        
        return jsonify({
            'success': True,
            'revenue': revenue_data,
            'currency': getattr(user, 'currency', 'USD')
        }), 200
    except Exception as e:
        current_app.logger.error(f'Error in get_revenue_stats: {str(e)}')
        current_app.logger.error(f'Traceback: {traceback.format_exc()}')
        return jsonify({
            'success': False,
            'error': f'Failed to load revenue stats: {str(e)}'
        }), 500

