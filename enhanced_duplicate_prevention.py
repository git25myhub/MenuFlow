#!/usr/bin/env python3
"""
Enhanced duplicate order prevention with additional features
"""

from flask import session, request, jsonify
from datetime import datetime, timedelta, timezone
import hashlib
import json
import logging

def generate_order_hash(order_data):
    """Generate a unique hash for order data"""
    order_string = json.dumps(order_data, sort_keys=True)
    return hashlib.md5(order_string.encode()).hexdigest()

def check_session_duplicate(order_hash, timeout_minutes=None):
    """Check if order hash exists in session within timeout (double-click protection)"""
    from duplicate_prevention_config import SESSION_DUPLICATE_WINDOW_MINUTES
    if timeout_minutes is None:
        timeout_minutes = SESSION_DUPLICATE_WINDOW_MINUTES
    if 'recent_orders' not in session:
        session['recent_orders'] = {}
    current_time = datetime.now(timezone.utc)
    # Clean old entries
    session['recent_orders'] = {
        hash_val: timestamp for hash_val, timestamp in session['recent_orders'].items()
        if (current_time - timestamp).total_seconds() < timeout_minutes * 60
    }
    # Check if current hash exists
    if order_hash in session['recent_orders']:
        return True
    # Add current hash
    session['recent_orders'][order_hash] = current_time
    return False

# After a successful order, clear the session hash for that order

def clear_session_duplicate(order_hash):
    if 'recent_orders' in session and order_hash in session['recent_orders']:
        del session['recent_orders'][order_hash]

def rate_limit_orders(ip_address, max_orders_per_minute=None):
    """Rate limit orders per IP address"""
    from duplicate_prevention_config import RATE_LIMIT_MAX_ORDERS_PER_MINUTE
    if max_orders_per_minute is None:
        max_orders_per_minute = RATE_LIMIT_MAX_ORDERS_PER_MINUTE
    """Rate limit orders per IP address"""
    if 'order_rate_limit' not in session:
        session['order_rate_limit'] = {}
    
    current_time = datetime.now()
    
    # Clean old entries
    session['order_rate_limit'] = {
        ip: timestamps for ip, timestamps in session['order_rate_limit'].items()
        if any((current_time - ts).total_seconds() < 60 for ts in timestamps)
    }
    
    if ip_address not in session['order_rate_limit']:
        session['order_rate_limit'][ip_address] = []
    
    # Remove timestamps older than 1 minute
    session['order_rate_limit'][ip_address] = [
        ts for ts in session['order_rate_limit'][ip_address]
        if (current_time - ts).total_seconds() < 60
    ]
    
    # Check rate limit
    if len(session['order_rate_limit'][ip_address]) >= max_orders_per_minute:
        return False
    
    # Add current timestamp
    session['order_rate_limit'][ip_address].append(current_time)
    return True

def enhanced_duplicate_check(order_data, user_id):
    """Enhanced duplicate checking with multiple layers"""
    from app import Order, db
    # Layer 1: Session-based double-click protection
    order_hash = generate_order_hash(order_data)
    if check_session_duplicate(order_hash):
        return {'is_duplicate': True, 'reason': 'session_duplicate', 'message': 'Order already submitted recently (double-click protection)'}
    # Layer 2: Database duplicate check (status-aware, timezone-aware)
    customer_name = order_data.get('customer_name', '')
    customer_phone = order_data.get('customer_phone', '')
    delivery_address = order_data.get('delivery_address', '')
    order_type = order_data.get('order_type', 'dine_in')
    table_number = order_data.get('table_number', '')
    total = order_data.get('total_amount', 0)
    from duplicate_prevention_config import DUPLICATE_DETECTION_WINDOW_MINUTES
    now_utc = datetime.now(timezone.utc)
    # Add logging for debugging
    logging.info(f"[DuplicateCheck] now_utc: {now_utc} (tzinfo={now_utc.tzinfo})")
    recent_duplicate = Order.query.filter(
        Order.restaurant_id == user_id,
        Order.customer_name == customer_name,
        Order.customer_phone == customer_phone,
        Order.delivery_address == delivery_address,
        Order.order_type == order_type,
        Order.table_number == table_number,
        Order.total_amount == total,
        Order.created_at >= now_utc - timedelta(minutes=DUPLICATE_DETECTION_WINDOW_MINUTES),
        Order.status.in_(['pending', 'processing'])
    ).first()
    if recent_duplicate:
        logging.info(f"[DuplicateCheck] Found recent duplicate: {recent_duplicate.id}, created_at={recent_duplicate.created_at} (tzinfo={getattr(recent_duplicate.created_at, 'tzinfo', None)})")
        return {
            'is_duplicate': True, 
            'reason': 'database_duplicate', 
            'message': 'This order is already being processed. Please wait until it is completed before submitting again.',
            'duplicate_order_id': recent_duplicate.id
        }
    # Layer 3: Rate limiting (relaxed: only for identical orders in short window)
    # (Optional: can be omitted if session duplicate is sufficient)
    # If you want to keep, add logic here
    return {'is_duplicate': False, 'order_hash': order_hash}

# Usage: after a successful order, call clear_session_duplicate(order_hash)
# Example (in your order creation route):
# result = enhanced_duplicate_check(order_data, user_id)
# if not result['is_duplicate']:
#     # ... create order ...
#     clear_session_duplicate(result['order_hash']) 