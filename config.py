import os

# Server Configuration
# Allow overriding the server URL and restaurant ID via environment variables for local dev
SERVER_URL = os.environ.get("SERVER_URL", "https://bluespace-restaurants.onrender.com")
RESTAURANT_ID = int(os.environ.get("RESTAURANT_ID", "2"))

# GPIO Pin Configuration (Legacy - for backward compatibility)
DINE_IN_LED_PIN = 17      # GPIO17
DELIVERY_LED_PIN = 27     # GPIO27
BUZZER_PIN = 22           # GPIO22

# Notification Configuration (Compatible with new hardware notifier)
NOTIFICATION_CONFIG = {
    "NEW_ORDER": {
        "led_pin": DINE_IN_LED_PIN,
        "buzzer_frequency": 440,      # A4 note
        "buzzer_duty_cycle": 50,      # 50% duty cycle
        "duration": 0.5,              # 0.5 seconds per cycle
        "repetitions": 3,             # 3 repetitions
        "pattern": "blink"            # Blinking pattern
    },
    
    "ORDER_READY": {
        "led_pin": DELIVERY_LED_PIN,
        "buzzer_frequency": 880,      # A5 note (higher pitch)
        "buzzer_duty_cycle": 25,      # 25% duty cycle (quieter)
        "duration": 1.0,              # 1 second per cycle
        "repetitions": 2,             # 2 repetitions
        "pattern": "pulse"            # Pulsing pattern
    },
    
    "ORDER_DELIVERED": {
        "led_pin": DELIVERY_LED_PIN,
        "buzzer_frequency": 660,      # E5 note
        "buzzer_duty_cycle": 30,      # 30% duty cycle
        "duration": 0.8,              # 0.8 seconds per cycle
        "repetitions": 1,             # 1 repetition
        "pattern": "solid"            # Solid light
    },
    
    "PAYMENT_RECEIVED": {
        "led_pin": DINE_IN_LED_PIN,   # Using same pin for payment
        "buzzer_frequency": 550,      # C#5 note
        "buzzer_duty_cycle": 40,      # 40% duty cycle
        "duration": 0.3,              # 0.3 seconds per cycle
        "repetitions": 4,             # 4 repetitions
        "pattern": "blink"            # Blinking pattern
    },
    
    "ERROR": {
        "led_pin": DINE_IN_LED_PIN,   # Using same pin for errors
        "buzzer_frequency": 200,      # Low frequency for errors
        "buzzer_duty_cycle": 75,      # 75% duty cycle (loud)
        "duration": 0.2,              # 0.2 seconds per cycle
        "repetitions": 5,             # 5 repetitions
        "pattern": "blink"            # Fast blinking
    },
    
    "WARNING": {
        "led_pin": DINE_IN_LED_PIN,   # Using same pin for warnings
        "buzzer_frequency": 300,      # Medium frequency for warnings
        "buzzer_duty_cycle": 60,      # 60% duty cycle
        "duration": 0.4,              # 0.4 seconds per cycle
        "repetitions": 3,             # 3 repetitions
        "pattern": "pulse"            # Pulsing pattern
    },
    
    "INFO": {
        "led_pin": DINE_IN_LED_PIN,   # Using same pin for info
        "buzzer_frequency": 800,      # High frequency for info
        "buzzer_duty_cycle": 20,      # 20% duty cycle (quiet)
        "duration": 0.6,              # 0.6 seconds per cycle
        "repetitions": 1,             # 1 repetition
        "pattern": "solid"            # Solid light
    }
}

# Performance Settings
PERFORMANCE_CONFIG = {
    "rate_limit_window": 1.0,         # Time window for rate limiting (seconds)
    "max_notifications_per_window": 3, # Maximum notifications per window
    "queue_max_size": 100,            # Maximum queue size
    "processing_timeout": 5.0,        # Timeout for processing thread (seconds)
    "hardware_timeout": 2.0,          # Timeout for hardware operations (seconds)
}

# Hardware Settings
HARDWARE_CONFIG = {
    "gpio_mode": "BCM",               # GPIO mode (BCM or BOARD)
    "pwm_frequency": 440,             # Default PWM frequency
    "pwm_duty_cycle": 0,              # Default PWM duty cycle
    "pin_initial_state": "LOW",       # Initial state for all pins
    "enable_pwm": True,               # Enable PWM for buzzer
    "enable_led": True,               # Enable LED notifications
    "enable_buzzer": True,            # Enable buzzer notifications
    # New: allow configuring active level depending on wiring
    "led_active_high": True,
    "buzzer_active_high": True,
}
