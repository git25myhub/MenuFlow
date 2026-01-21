#!/usr/bin/env python3
"""
Detailed performance analysis for duplicate order prevention system
"""

import sqlite3
from datetime import datetime, timedelta
from duplicate_prevention_config import get_config

def analyze_duplicate_patterns():
    """Analyze patterns in duplicate orders to understand root causes"""
    print("🔍 DETAILED DUPLICATE ORDER ANALYSIS")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('restaurant.db')
        cursor = conn.cursor()
        
        # Get orders from last 24 hours
        yesterday = datetime.now() - timedelta(days=1)
        
        # Get all orders with duplicates
        cursor.execute("""
            SELECT 
                customer_name,
                customer_phone,
                order_type,
                table_number,
                total_amount,
                created_at,
                COUNT(*) as duplicate_count
            FROM `order`
            WHERE created_at >= ?
            GROUP BY 
                customer_name,
                customer_phone,
                order_type,
                table_number,
                total_amount
            HAVING COUNT(*) > 1
            ORDER BY duplicate_count DESC, created_at DESC
        """, (yesterday.strftime('%Y-%m-%d %H:%M:%S'),))
        
        duplicates = cursor.fetchall()
        
        if not duplicates:
            print("✅ No duplicate patterns found in the last 24 hours!")
            return
        
        print(f"📊 Found {len(duplicates)} duplicate patterns:")
        print()
        
        total_duplicate_orders = 0
        for dup in duplicates:
            customer_name, phone, order_type, table_num, amount, created_at, count = dup
            total_duplicate_orders += count
            
            print(f"👤 Customer: {customer_name} ({phone})")
            print(f"   📋 Order Type: {order_type}")
            print(f"   🏷️  Table: {table_num}")
            print(f"   💰 Amount: ${amount}")
            print(f"   📅 Created: {created_at}")
            print(f"   🔄 Duplicate Count: {count}")
            print(f"   ⏱️  Time Window: {get_time_window(created_at)}")
            print()
        
        # Analyze timing patterns
        analyze_timing_patterns(cursor, yesterday)
        
        # Analyze customer patterns
        analyze_customer_patterns(cursor, yesterday)
        
        # Suggest optimizations
        suggest_optimizations(duplicates, total_duplicate_orders)
        
    except Exception as e:
        print(f"❌ Error analyzing duplicates: {str(e)}")
    finally:
        if conn:
            conn.close()

def analyze_timing_patterns(cursor, yesterday):
    """Analyze timing patterns in duplicate orders"""
    print("⏱️  TIMING PATTERN ANALYSIS:")
    print("-" * 30)
    
    cursor.execute("""
        SELECT 
            customer_name,
            customer_phone,
            created_at,
            COUNT(*) as order_count
        FROM `order`
        WHERE created_at >= ?
        GROUP BY customer_name, customer_phone
        HAVING COUNT(*) > 1
        ORDER BY order_count DESC
    """, (yesterday.strftime('%Y-%m-%d %H:%M:%S'),))
    
    rapid_orders = cursor.fetchall()
    
    if rapid_orders:
        print("🚨 Rapid Order Patterns (same customer, multiple orders):")
        for order in rapid_orders:
            name, phone, created_at, count = order
            print(f"   • {name} ({phone}): {count} orders at {created_at}")
    else:
        print("✅ No rapid order patterns detected")
    print()

def analyze_customer_patterns(cursor, yesterday):
    """Analyze customer-specific patterns"""
    print("👥 CUSTOMER PATTERN ANALYSIS:")
    print("-" * 30)
    
    cursor.execute("""
        SELECT 
            customer_name,
            customer_phone,
            COUNT(*) as total_orders,
            COUNT(DISTINCT total_amount) as unique_amounts
        FROM `order`
        WHERE created_at >= ?
        GROUP BY customer_name, customer_phone
        HAVING COUNT(*) > 1
        ORDER BY total_orders DESC
    """, (yesterday.strftime('%Y-%m-%d %H:%M:%S'),))
    
    customers = cursor.fetchall()
    
    if customers:
        print("👤 Customers with multiple orders:")
        for customer in customers:
            name, phone, total, unique = customer
            if total == unique:
                print(f"   • {name} ({phone}): {total} orders - All different amounts ✅")
            else:
                print(f"   • {name} ({phone}): {total} orders - {total - unique} duplicates ⚠️")
    else:
        print("✅ No customer patterns detected")
    print()

def suggest_optimizations(duplicates, total_duplicate_orders):
    """Suggest specific optimizations based on analysis"""
    print("💡 OPTIMIZATION SUGGESTIONS:")
    print("-" * 30)
    
    config = get_config()
    current_window = config['duplicate_detection_window_minutes']
    current_rate_limit = config['rate_limit_max_orders_per_minute']
    
    # Analyze patterns
    rapid_duplicates = sum(1 for dup in duplicates if dup[6] > 2)  # More than 2 duplicates
    same_amount_duplicates = sum(1 for dup in duplicates if dup[4] == duplicates[0][4])  # Same amount
    
    suggestions = []
    
    if rapid_duplicates > 0:
        suggestions.append("🚨 Multiple rapid duplicates detected - Consider reducing rate limit")
        suggestions.append(f"   Current: {current_rate_limit} orders/minute → Suggested: 1 order/minute")
    
    if same_amount_duplicates > len(duplicates) * 0.5:  # More than 50% same amount
        suggestions.append("💰 Many duplicates have same amount - Strengthen amount-based detection")
        suggestions.append(f"   Current window: {current_window} minutes → Suggested: 15 minutes")
    
    if total_duplicate_orders > 10:
        suggestions.append("📈 High duplicate volume - Consider stricter session management")
        suggestions.append("   Suggested: Reduce session timeout to 5 minutes")
    
    if not suggestions:
        suggestions.append("✅ Current settings appear appropriate for detected patterns")
        suggestions.append("   Monitor for 24-48 hours to gather more data")
    
    for suggestion in suggestions:
        print(suggestion)
    
    print()
    print("🔧 RECOMMENDED ACTIONS:")
    print("-" * 30)
    print("1. Run: python optimize_prevention.py")
    print("2. Monitor for 24 hours")
    print("3. Run: python system_status_report.py")
    print("4. Adjust settings based on new data")

def get_time_window(created_at):
    """Get time window for order creation"""
    try:
        order_time = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        diff = now - order_time
        return f"{diff.total_seconds() / 60:.1f} minutes ago"
    except:
        return "Unknown"

if __name__ == "__main__":
    analyze_duplicate_patterns() 