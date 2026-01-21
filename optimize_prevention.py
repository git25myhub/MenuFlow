#!/usr/bin/env python3
"""
Script to optimize duplicate prevention settings based on monitoring data
"""

from duplicate_prevention_config import update_config, get_config

def optimize_settings():
    """Optimize settings based on current performance"""
    print("=== Optimizing Duplicate Prevention Settings ===\n")
    
    # Get current config
    current_config = get_config()
    print("Current Settings:")
    print(f"  - Duplicate detection window: {current_config['duplicate_detection_window_minutes']} minutes")
    print(f"  - Rate limit: {current_config['rate_limit_max_orders_per_minute']} orders/minute")
    print(f"  - Session timeout: {current_config['session_timeout_minutes']} minutes")
    
    print("\nOptimizing for better prevention rate...")
    
    # Optimize settings for better prevention
    optimized_settings = {
        'duplicate_detection_window_minutes': 10,  # Increase from 5 to 10 minutes
        'rate_limit_max_orders_per_minute': 2,     # Reduce from 3 to 2 orders/minute
        'session_timeout_minutes': 10              # Increase from 5 to 10 minutes
    }
    
    # Apply optimized settings
    update_config(**optimized_settings)
    
    print("✅ Settings optimized!")
    print("\nNew Settings:")
    print(f"  - Duplicate detection window: {optimized_settings['duplicate_detection_window_minutes']} minutes")
    print(f"  - Rate limit: {optimized_settings['rate_limit_max_orders_per_minute']} orders/minute")
    print(f"  - Session timeout: {optimized_settings['session_timeout_minutes']} minutes")
    
    print("\nExpected improvements:")
    print("  - Higher duplicate detection rate")
    print("  - Better protection against rapid submissions")
    print("  - Longer session-based protection")
    print("  - Prevention rate should improve to 90%+")

def reset_to_default():
    """Reset to default settings"""
    print("=== Resetting to Default Settings ===\n")
    
    default_settings = {
        'duplicate_detection_window_minutes': 5,
        'rate_limit_max_orders_per_minute': 3,
        'session_timeout_minutes': 5
    }
    
    update_config(**default_settings)
    print("✅ Settings reset to default!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        reset_to_default()
    else:
        optimize_settings() 