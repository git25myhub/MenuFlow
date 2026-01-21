#!/usr/bin/env python3
"""
Quick optimization script to improve duplicate prevention rate
"""

def quick_optimize():
    """Apply quick optimizations based on current performance"""
    print("🚀 QUICK OPTIMIZATION - IMPROVING PREVENTION RATE")
    print("=" * 50)
    
    # Read current config
    with open('duplicate_prevention_config.py', 'r') as f:
        content = f.read()
    
    # Apply aggressive optimizations
    optimizations = {
        'DUPLICATE_DETECTION_WINDOW_MINUTES = 10': 'DUPLICATE_DETECTION_WINDOW_MINUTES = 15',
        'RATE_LIMIT_MAX_ORDERS_PER_MINUTE = 2': 'RATE_LIMIT_MAX_ORDERS_PER_MINUTE = 1',
        'SESSION_TIMEOUT_MINUTES = 10': 'SESSION_TIMEOUT_MINUTES = 5'
    }
    
    optimized_content = content
    for old, new in optimizations.items():
        optimized_content = optimized_content.replace(old, new)
    
    # Write optimized config
    with open('duplicate_prevention_config.py', 'w') as f:
        f.write(optimized_content)
    
    print("✅ Applied Quick Optimizations:")
    print("   • Detection Window: 10 → 15 minutes")
    print("   • Rate Limit: 2 → 1 orders/minute")
    print("   • Session Timeout: 10 → 5 minutes")
    print()
    print("🎯 Expected Improvement:")
    print("   • Prevention rate should increase to 80%+")
    print("   • More aggressive duplicate detection")
    print("   • Stricter rate limiting")
    print()
    print("📊 Next Steps:")
    print("   1. Monitor system for 2-4 hours")
    print("   2. Run: python system_status_report.py")
    print("   3. Check if prevention rate improves")

if __name__ == "__main__":
    quick_optimize() 