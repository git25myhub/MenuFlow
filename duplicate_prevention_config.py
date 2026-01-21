#!/usr/bin/env python3
"""
Configuration file for enhanced duplicate order prevention
"""

# Duplicate Detection Settings
DUPLICATE_DETECTION_WINDOW_MINUTES = 15  # Time window to check for database duplicates (status-aware)
SESSION_DUPLICATE_WINDOW_MINUTES = 2     # Short window for double-click/session duplicate protection
RATE_LIMIT_MAX_ORDERS_PER_MINUTE = 1    # Maximum orders per minute per IP
SESSION_TIMEOUT_MINUTES = 5             # (legacy, not used for double-click protection)

# Database Settings
DATABASE_DUPLICATE_CHECK_ENABLED = True
DATABASE_INDEXES_ENABLED = True

# Frontend Settings
FRONTEND_BUTTON_DISABLE_ENABLED = True
FRONTEND_LOADING_STATE_ENABLED = True
FRONTEND_TOAST_NOTIFICATIONS_ENABLED = True

# Logging Settings
LOG_DUPLICATE_ATTEMPTS = True
LOG_RATE_LIMIT_VIOLATIONS = True
LOG_SESSION_DUPLICATES = True

# Performance Settings
CACHE_SESSION_DATA = True
CLEANUP_OLD_SESSION_DATA = True
CLEANUP_INTERVAL_MINUTES = 10

# Error Messages
ERROR_MESSAGES = {
    'session_duplicate': 'This order has already been submitted in this session. Please check your order status.',
    'rate_limit': 'Too many orders submitted. Please wait a moment before trying again.',
    'database_duplicate': 'This order has already been submitted. Please check your order status.',
    'unknown': 'An error occurred while processing your order. Please try again.'
}

# Success Messages
SUCCESS_MESSAGES = {
    'order_created': 'Order placed successfully!',
    'duplicate_prevented': 'Duplicate order prevented successfully.'
}

def get_config():
    """Get the current configuration"""
    return {
        'duplicate_detection_window_minutes': DUPLICATE_DETECTION_WINDOW_MINUTES,
        'rate_limit_max_orders_per_minute': RATE_LIMIT_MAX_ORDERS_PER_MINUTE,
        'session_timeout_minutes': SESSION_TIMEOUT_MINUTES,
        'database_duplicate_check_enabled': DATABASE_DUPLICATE_CHECK_ENABLED,
        'database_indexes_enabled': DATABASE_INDEXES_ENABLED,
        'frontend_button_disable_enabled': FRONTEND_BUTTON_DISABLE_ENABLED,
        'frontend_loading_state_enabled': FRONTEND_LOADING_STATE_ENABLED,
        'frontend_toast_notifications_enabled': FRONTEND_TOAST_NOTIFICATIONS_ENABLED,
        'log_duplicate_attempts': LOG_DUPLICATE_ATTEMPTS,
        'log_rate_limit_violations': LOG_RATE_LIMIT_VIOLATIONS,
        'log_session_duplicates': LOG_SESSION_DUPLICATES,
        'cache_session_data': CACHE_SESSION_DATA,
        'cleanup_old_session_data': CLEANUP_OLD_SESSION_DATA,
        'cleanup_interval_minutes': CLEANUP_INTERVAL_MINUTES,
        'error_messages': ERROR_MESSAGES,
        'success_messages': SUCCESS_MESSAGES
    }

def update_config(**kwargs):
    """Update configuration values"""
    global DUPLICATE_DETECTION_WINDOW_MINUTES, RATE_LIMIT_MAX_ORDERS_PER_MINUTE
    global SESSION_TIMEOUT_MINUTES, DATABASE_DUPLICATE_CHECK_ENABLED
    global FRONTEND_BUTTON_DISABLE_ENABLED, FRONTEND_LOADING_STATE_ENABLED
    
    if 'duplicate_detection_window_minutes' in kwargs:
        DUPLICATE_DETECTION_WINDOW_MINUTES = kwargs['duplicate_detection_window_minutes']
    if 'rate_limit_max_orders_per_minute' in kwargs:
        RATE_LIMIT_MAX_ORDERS_PER_MINUTE = kwargs['rate_limit_max_orders_per_minute']
    if 'session_timeout_minutes' in kwargs:
        SESSION_TIMEOUT_MINUTES = kwargs['session_timeout_minutes']
    if 'database_duplicate_check_enabled' in kwargs:
        DATABASE_DUPLICATE_CHECK_ENABLED = kwargs['database_duplicate_check_enabled']
    if 'frontend_button_disable_enabled' in kwargs:
        FRONTEND_BUTTON_DISABLE_ENABLED = kwargs['frontend_button_disable_enabled']
    if 'frontend_loading_state_enabled' in kwargs:
        FRONTEND_LOADING_STATE_ENABLED = kwargs['frontend_loading_state_enabled']
    
    print("✅ Configuration updated successfully!")

if __name__ == "__main__":
    print("=== Duplicate Prevention Configuration ===")
    config = get_config()
    for key, value in config.items():
        print(f"{key}: {value}") 