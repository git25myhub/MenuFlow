from app import app, db
from models import Order
import json

with app.app_context():
    zero_total_orders = []
    missing_price_orders = []
    delivered_orders = Order.query.filter_by(status='delivered').all()
    for order in delivered_orders:
        try:
            items = json.loads(order.items)
        except Exception as e:
            print(f"Order ID {order.id} has invalid items JSON: {e}")
            continue
        total = sum(item.get('price', 0) * item.get('quantity', 0) for item in items)
        if total == 0:
            zero_total_orders.append(order)
        for item in items:
            if 'price' not in item or item.get('price', 0) == 0:
                missing_price_orders.append(order)
                break
    print("\n--- Delivered Orders with Total $0.00 ---")
    for order in zero_total_orders:
        print(f"Order ID: {order.id}, Table: {order.table_number}, Items: {order.items}")
    print("\n--- Delivered Orders with Missing/Zero Price ---")
    for order in missing_price_orders:
        print(f"Order ID: {order.id}, Table: {order.table_number}, Items: {order.items}") 