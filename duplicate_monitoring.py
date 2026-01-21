#!/usr/bin/env python3
"""
Monitoring script for duplicate order prevention
"""

from app import app, db, Order
from datetime import datetime, timedelta
from sqlalchemy import func

def get_duplicate_prevention_stats():
    """Get statistics about duplicate order prevention"""
    with app.app_context():
        try:
            # Get orders from last 24 hours
            yesterday = datetime.now() - timedelta(days=1)
            
            # Total orders in last 24 hours
            total_orders = Order.query.filter(
                Order.created_at >= yesterday
            ).count()
            
            # Potential duplicates (same customer, same items, within 5 minutes)
            potential_duplicates = db.session.query(
                Order.customer_name,
                Order.customer_phone,
                Order.total_amount,
                func.count(Order.id).label('count')
            ).filter(
                Order.created_at >= yesterday
            ).group_by(
                Order.customer_name,
                Order.customer_phone,
                Order.total_amount
            ).having(func.count(Order.id) > 1).all()
            
            # Actual duplicates (orders with same details within 5 minutes)
            actual_duplicates = 0
            for dup in potential_duplicates:
                customer_orders = Order.query.filter(
                    Order.customer_name == dup.customer_name,
                    Order.customer_phone == dup.customer_phone,
                    Order.total_amount == dup.total_amount,
                    Order.created_at >= yesterday
                ).order_by(Order.created_at).all()
                
                # Check for orders within 5 minutes of each other
                for i in range(len(customer_orders) - 1):
                    time_diff = customer_orders[i+1].created_at - customer_orders[i].created_at
                    if time_diff.total_seconds() <= 300:  # 5 minutes
                        actual_duplicates += 1
            
            # Prevention rate
            prevention_rate = 0
            if total_orders > 0:
                prevention_rate = ((total_orders - actual_duplicates) / total_orders) * 100
            
            return {
                'total_orders_24h': total_orders,
                'potential_duplicates': len(potential_duplicates),
                'actual_duplicates': actual_duplicates,
                'prevention_rate': round(prevention_rate, 2),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting stats: {str(e)}")
            return None

def print_monitoring_report():
    """Print a monitoring report"""
    stats = get_duplicate_prevention_stats()
    if stats:
        print("=== Duplicate Order Prevention Monitoring Report ===")
        print(f"📊 Total Orders (24h): {stats['total_orders_24h']}")
        print(f"⚠️  Potential Duplicates: {stats['potential_duplicates']}")
        print(f"🚫 Actual Duplicates: {stats['actual_duplicates']}")
        print(f"✅ Prevention Rate: {stats['prevention_rate']}%")
        print(f"🕐 Report Time: {stats['timestamp']}")
        
        if stats['prevention_rate'] >= 95:
            print("🎉 Excellent! Duplicate prevention is working very well!")
        elif stats['prevention_rate'] >= 80:
            print("👍 Good! Duplicate prevention is working well.")
        else:
            print("⚠️  Attention needed: Duplicate prevention may need improvement.")
    else:
        print("❌ Could not generate monitoring report")

if __name__ == "__main__":
    print_monitoring_report() 