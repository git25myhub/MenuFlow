import os
os.environ["SDL_AUDIODRIVER"] = "dummy"

#!/usr/bin/env python3
"""
Hardware Notifier for BlueSpace Restaurants
Raspberry Pi 4B Integration with LED, Buzzer, and Display System

This module provides hardware notification capabilities for restaurant order management,
including LED indicators, buzzer alerts, and a display system for kitchen staff.
"""

import logging
import time
import random
import json
import sys
import signal
import atexit
import socket
import traceback
from logging.handlers import RotatingFileHandler
from http.server import BaseHTTPRequestHandler, HTTPServer
import socketserver

# Use gevent-compatible threading instead of standard threading
try:
    from gevent import monkey
    monkey.patch_thread()
    import threading
except ImportError:
    import threading

import queue
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List
import requests
from dataclasses import dataclass
from collections import deque

# GPIO imports for Raspberry Pi
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("Warning: RPi.GPIO not available. Running in simulation mode.")
else:
    try:
        # Suppress noisy 'channel already in use' runtime warnings
        GPIO.setwarnings(False)
    except Exception:
        pass

# Display imports
print("Attempting to import display libraries...")
try:
    print("Importing PIL...")
    from PIL import Image, ImageDraw, ImageFont
    print("PIL imported successfully")
    print("Importing pygame...")
    import pygame
    print("Pygame imported successfully")
    DISPLAY_AVAILABLE = True
    print(f"✓ Display imports successful: DISPLAY_AVAILABLE={DISPLAY_AVAILABLE}")
except ImportError as e:
    DISPLAY_AVAILABLE = False
    print(f"✗ Display imports failed: {e}")
    print("Warning: PIL/pygame not available. Display features disabled.")
except Exception as e:
    DISPLAY_AVAILABLE = False
    print(f"✗ Unexpected error during display imports: {e}")
    print("Warning: Display features disabled due to unexpected error")

# Configuration
from config import NOTIFICATION_CONFIG, PERFORMANCE_CONFIG, HARDWARE_CONFIG, SERVER_URL as CFG_SERVER_URL, RESTAURANT_ID as CFG_RESTAURANT_ID, BUZZER_PIN as CFG_BUZZER_PIN

# Setup logging with rotation
_file_handler = RotatingFileHandler('hardware_notifier.log', maxBytes=1_000_000, backupCount=3)
_stream_handler = logging.StreamHandler()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[_file_handler, _stream_handler]
)

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            'ts': self.formatTime(record, datefmt='%Y-%m-%dT%H:%M:%S%z'),
            'logger': record.name,
            'level': record.levelname,
            'msg': record.getMessage(),
        }
        # Attach extra fields if present
        for key, value in getattr(record, '__dict__', {}).items():
            if key not in ('name','msg','args','levelname','levelno','pathname','filename','module','exc_info','exc_text','stack_info','lineno','funcName','created','msecs','relativeCreated','thread','threadName','processName','process'):
                payload[key] = value
        return json.dumps(payload, ensure_ascii=False)

try:
    _json_handler = RotatingFileHandler('hardware_notifier.jsonl', maxBytes=1_000_000, backupCount=3)
    _json_handler.setFormatter(JSONFormatter())
    logging.getLogger('').addHandler(_json_handler)
except Exception as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Failed to initialize JSON log handler: {e}")
logger = logging.getLogger(__name__)

class NotificationType(Enum):
    """Enumeration of notification types"""
    NEW_ORDER = "NEW_ORDER"
    ORDER_READY = "ORDER_READY"
    ORDER_DELIVERED = "ORDER_DELIVERED"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"

@dataclass
class Notification:
    """Data class for notification objects"""
    type: NotificationType
    priority: int
    metadata: Dict[str, Any]
    timestamp: datetime
    processed: bool = False

class HardwareNotifier:
    """
    Hardware notification system for Raspberry Pi 4B
    
    Features:
    - LED indicators for different notification types
    - Buzzer alerts with configurable patterns
    - Display system for kitchen staff
    - Real-time order monitoring
    - Performance optimization and rate limiting
    """
    
    def __init__(self, simulation_mode: bool = False):
        self.simulation_mode = simulation_mode
        self.notification_queue = queue.PriorityQueue(maxsize=PERFORMANCE_CONFIG.get("queue_max_size", 100))
        self.processing_thread = None
        self.running = False
        self.last_notification_time = {}
        self.rate_limit_window = PERFORMANCE_CONFIG.get("rate_limit_window", 1.0)
        self.max_notifications = PERFORMANCE_CONFIG.get("max_notifications_per_window", 3)
        self.internet_available = True  # Assume available at start
        self.fetch_backoff_until = 0.0
        self.fetch_backoff_seconds = 0.0
        # Force simulation on non-Raspberry Pi platforms or when requested via env
        try:
            if str(os.environ.get('SIMULATION_MODE', '')).strip().lower() in ('1', 'true', 'yes', 'on'):
                self.simulation_mode = True
            elif not GPIO_AVAILABLE or sys.platform.startswith('win') or sys.platform == 'darwin':
                self.simulation_mode = True
        except Exception:
            pass
        # Server/restaurant configuration from config.py only
        self.server_url = CFG_SERVER_URL
        self.restaurant_id = CFG_RESTAURANT_ID
        # Socket.IO client
        self.sio = None
        # Shutdown coordination for background threads
        try:
            self._shutdown_event = threading.Event()
        except Exception:
            self._shutdown_event = None
        # Health server
        self.health_server = None
        self.health_thread = None
        
        # Hardware components
        self.led_pins = {}
        self.buzzer_pin = None
        self.pwm = None
        # Active level configuration (allows wiring either sourcing or sinking)
        try:
            self.led_active_high = bool(HARDWARE_CONFIG.get('led_active_high', True))
            self.buzzer_active_high = bool(HARDWARE_CONFIG.get('buzzer_active_high', True))
        except Exception:
            self.led_active_high = True
            self.buzzer_active_high = True
        
        # Display system
        self.display_surface = None
        self.display_thread = None
        self.orders_to_display = deque(maxlen=50)
        # No sliding; render full grid view always
        self.current_slide = 0
        self.slide_duration = 0
        self.display_max_items = int(os.environ.get('DISPLAY_MAX_ITEMS_PER_CARD', '5'))
        self.display_max_orders = int(os.environ.get('DISPLAY_MAX_ORDERS', '12'))
        self.display_split_by_type = os.environ.get('DISPLAY_SPLIT_BY_TYPE', 'false').lower() == 'true'
        self.stale_yellow_seconds = int(os.environ.get('DISPLAY_STALE_YELLOW_SEC', '30'))
        self.stale_red_seconds = int(os.environ.get('DISPLAY_STALE_RED_SEC', '120'))
        self.last_orders_update_time = 0.0
        # Delivered flash overlay configuration
        self.delivered_flash_seconds = float(os.environ.get('DISPLAY_DELIVERED_FLASH_SEC', '1.2'))
        self.recent_deliveries = deque(maxlen=20)  # entries: {order_id, started_at, expires_at}
        # Fade-out animation for delivered order cards
        self.delivered_card_fade_seconds = float(os.environ.get('DISPLAY_DELIVERED_CARD_FADE_SEC', '1.2'))
        self.fading_orders: Dict[Any, Dict[str, Any]] = {}
        # Orders refresh (polling) for real-time fallback and initial population
        self.refresh_interval_seconds = float(os.environ.get('ORDERS_REFRESH_SEC', '3'))
        self.refresh_thread = None
        # Previous orders snapshot for delta-based notifications
        self.prev_orders_by_id: Dict[Any, Dict[str, Any]] = {}
        
        # Initialize hardware
        self._initialize_hardware()
        try:
            logger.info(f"Config: server_url={self.server_url} restaurant_id={self.restaurant_id} simulation_mode={self.simulation_mode}")
        except Exception:
            pass
        
        # Start processing threads
        self._start_processing()
        # Start watchdog to keep threads healthy
        try:
            self.watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True, name="HardwareNotifier-Watchdog")
            self.watchdog_thread.start()
        except Exception as e:
            logger.warning(f"Failed to start watchdog thread: {e}")
        # Start background services only once (avoid Flask reloader child processes)
        try:
            is_reloader_child = str(os.environ.get('WERKZEUG_RUN_MAIN', '')).strip().lower() == 'true'
        except Exception:
            is_reloader_child = False
        is_main = not is_reloader_child
        if is_main:
            # Start Socket.IO client (best-effort)
            try:
                self._start_socket()
            except Exception as e:
                logger.warning(f"Failed to start Socket.IO client: {e}")
            # Start health server
            try:
                self._start_health_server()
            except Exception as e:
                logger.warning(f"Failed to start health server: {e}")
        
        logger.info(f"Hardware Notifier initialized (simulation_mode={simulation_mode})")
    
    def _initialize_hardware(self):
        """Initialize GPIO pins and hardware components"""
        if self.simulation_mode or not GPIO_AVAILABLE:
            if not self.simulation_mode:
                self.simulation_mode = True
            logger.info("Running in simulation mode - hardware disabled")
            return
        
        try:
            # Set GPIO mode
            gpio_mode = HARDWARE_CONFIG.get("gpio_mode", "BCM")
            if gpio_mode == "BCM":
                GPIO.setmode(GPIO.BCM)
            else:
                GPIO.setmode(GPIO.BOARD)
            
            # Initialize LED pins
            for notification_type, config in NOTIFICATION_CONFIG.items():
                led_pin = config.get("led_pin")
                if led_pin is not None:
                    GPIO.setup(led_pin, GPIO.OUT)
                    # Start with LED off regardless of active level
                    GPIO.output(led_pin, GPIO.HIGH if not self.led_active_high else GPIO.LOW)
                    self.led_pins[notification_type] = led_pin
            
            # Initialize buzzer pin
            buzzer_pin = CFG_BUZZER_PIN if isinstance(CFG_BUZZER_PIN, int) else 22
            GPIO.setup(buzzer_pin, GPIO.OUT)
            self.buzzer_pin = buzzer_pin
            
            # Initialize PWM for buzzer
            if HARDWARE_CONFIG.get("enable_pwm", True):
                self.pwm = GPIO.PWM(buzzer_pin, HARDWARE_CONFIG.get("pwm_frequency", 440))
                self.pwm.start(0)  # Start with 0% duty cycle
            
            logger.info("Hardware initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize hardware: {e}")
            self.simulation_mode = True
    
    def _start_processing(self):
        """Start the notification processing thread"""
        self.running = True
        
        # Create processing thread with gevent compatibility
        try:
            self.processing_thread = threading.Thread(target=self._process_notifications, daemon=True, name="HardwareNotifier-Processing")
            self.processing_thread.start()
            logger.info("Processing thread started successfully")
        except Exception as e:
            logger.error(f"Failed to start processing thread: {e}")
            self.running = False
            return
        
        # Start periodic orders refresh regardless of display availability
        try:
            # Initial fetch to populate display immediately
            try:
                initial_orders = self._fetch_undelivered_orders()
                if initial_orders is not None:
                    self.orders_to_display.clear()
                    self.orders_to_display.extend(initial_orders)
                    self.last_orders_update_time = time.time()
                    # Initialize previous snapshot for delta notifications
                    try:
                        self.prev_orders_by_id = {o.get('id'): o for o in list(initial_orders)}
                    except Exception:
                        self.prev_orders_by_id = {}
            except Exception:
                pass
            self.refresh_thread = threading.Thread(target=self._orders_refresh_loop, daemon=True, name="HardwareNotifier-OrdersRefresh")
            self.refresh_thread.start()
            logger.info("Orders refresh thread started")
        except Exception as e:
            logger.error(f"Failed to start orders refresh thread: {e}")
        
        # Start display thread if display is available and not in simulation mode
        logger.info(f"Display thread check: DISPLAY_AVAILABLE={DISPLAY_AVAILABLE}, simulation_mode={self.simulation_mode}")
        logger.info(f"About to start display thread...")
        if DISPLAY_AVAILABLE and not self.simulation_mode:
            logger.info("Conditions met, attempting to start display thread...")
            try:
                logger.info("Creating display thread...")
                self.display_thread = threading.Thread(target=self._display_orders, daemon=True, name="HardwareNotifier-Display")
                logger.info("Starting display thread...")
                self.display_thread.start()
                logger.info("Display thread started successfully")
                # Wait a moment to confirm the thread is actually running
                time.sleep(0.5)
                if self.display_thread.is_alive():
                    logger.info("Display thread confirmed running and healthy")
                else:
                    logger.error("Display thread failed to start properly")
            except Exception as e:
                logger.error(f"Failed to start display thread: {e}")
                logger.error(f"Display thread error traceback: {traceback.format_exc()}")
                # Try to get more specific error information
                try:
                    import pygame
                    if pygame.get_init():
                        logger.info("Pygame is initialized but display thread failed")
                    else:
                        logger.error("Pygame failed to initialize")
                except Exception as pygame_error:
                    logger.error(f"Pygame status check failed: {pygame_error}")
        else:
            logger.info("Display thread not started (simulation mode or display not available)")
            if not DISPLAY_AVAILABLE:
                logger.warning("DISPLAY_AVAILABLE is False - pygame import may have failed")
            if self.simulation_mode:
                logger.warning("Running in simulation mode - display disabled")
    
    def notify(self, notification_type: NotificationType, priority: int = 1, metadata: Dict[str, Any] = None) -> bool:
        """
        Queue a notification for processing
        
        Args:
            notification_type: Type of notification
            priority: Priority level (1-5, higher is more important)
            metadata: Additional data for the notification
            
        Returns:
            bool: True if notification was queued successfully
        """
        try:
            # Rate limiting check
            if not self._check_rate_limit(notification_type):
                logger.warning(f"Rate limit exceeded for {notification_type.value}")
                return False
            
            # Create notification object
            notification = Notification(
                type=notification_type,
                priority=priority,
                metadata=metadata or {},
                timestamp=datetime.now()
            )
            
            # Add to queue with priority (lower number = higher priority)
            try:
                self.notification_queue.put_nowait((5 - priority, notification))
            except queue.Full:
                # Queue is full: try to make room by dropping lowest-priority non-critical notification
                if self._try_evict_lower_priority(5 - priority):
                    try:
                        self.notification_queue.put_nowait((5 - priority, notification))
                    except queue.Full:
                        logger.warning(f"Queue full, dropping notification: {notification_type.value}")
                        return False
                else:
                    logger.warning(f"Queue full, dropping notification: {notification_type.value}")
                    return False
            
            # Update rate limiting
            self._update_rate_limit(notification_type)
            
            logger.info(f"Notification queued: {notification_type.value} (priority: {priority})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to queue notification: {e}")
            return False
    
    def _check_rate_limit(self, notification_type: NotificationType) -> bool:
        """Check if notification is within rate limits"""
        now = time.time()
        notification_key = notification_type.value
        
        if notification_key not in self.last_notification_time:
            return True
        
        # Check if enough time has passed
        time_since_last = now - self.last_notification_time[notification_key]
        return time_since_last >= self.rate_limit_window
    
    def _update_rate_limit(self, notification_type: NotificationType):
        """Update rate limiting timestamp"""
        self.last_notification_time[notification_type.value] = time.time()
    
    def _process_notifications(self):
        """Process notifications from the queue"""
        logger.info("Notification processing thread started")
        while self.running:
            try:
                # Get notification from queue with timeout
                priority, notification = self.notification_queue.get(timeout=1.0)
                
                # Process the notification
                self._execute_notification(notification)
                
                # Mark as processed
                notification.processed = True
                self.notification_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing notification: {e}")
                # Continue processing even if one notification fails
                continue
        
        logger.info("Notification processing thread stopped")

    def _try_evict_lower_priority(self, incoming_priority_value: int) -> bool:
        """Attempt to evict a lower-priority item to make space. Returns True if evicted."""
        try:
            with self.notification_queue.mutex:
                # Items are tuples (priority_value, Notification)
                # Higher priority_value means lower actual priority (since we invert with 5-priority)
                if not self.notification_queue.queue:
                    return False
                # Find the worst (max priority_value)
                worst_idx = None
                worst_value = -1
                for idx, (pval, notif) in enumerate(self.notification_queue.queue):
                    if pval > worst_value:
                        worst_value = pval
                        worst_idx = idx
                if worst_idx is not None and worst_value >= incoming_priority_value:
                    # Evict the worst to make room
                    self.notification_queue.queue.pop(worst_idx)
                    return True
                return False
        except Exception as e:
            logger.warning(f"Eviction failed: {e}")
            return False
    
    def _execute_notification(self, notification: Notification):
        """Execute a notification on hardware"""
        try:
            config = NOTIFICATION_CONFIG.get(notification.type.value, {})
            
            # Get configuration values
            led_pin = config.get("led_pin")
            buzzer_freq = config.get("buzzer_frequency", 440)
            buzzer_duty = config.get("buzzer_duty_cycle", 50)
            duration = config.get("duration", 0.5)
            repetitions = config.get("repetitions", 1)
            pattern = config.get("pattern", "blink")
            
            logger.info(f"Executing notification: {notification.type.value}")
            
            # Execute LED pattern
            if led_pin and HARDWARE_CONFIG.get("enable_led", True):
                self._execute_led_pattern(led_pin, pattern, duration, repetitions)
            
            # Execute buzzer pattern
            if HARDWARE_CONFIG.get("enable_buzzer", True):
                self._execute_buzzer_pattern(buzzer_freq, buzzer_duty, duration, repetitions)
            
            # Update display if it's an order-related notification
            if notification.type in [NotificationType.NEW_ORDER, NotificationType.ORDER_READY]:
                self._update_order_display(notification)
            
        except Exception as e:
            logger.error(f"Error executing notification: {e}")
    
    def _execute_led_pattern(self, pin: int, pattern: str, duration: float, repetitions: int):
        """Execute LED pattern"""
        if self.simulation_mode or not GPIO_AVAILABLE:
            logger.info(f"SIMULATION: LED {pin} pattern '{pattern}' for {duration}s, {repetitions} times")
            return
        
        try:
            for _ in range(repetitions):
                if pattern == "blink":
                    GPIO.output(pin, GPIO.HIGH)
                    time.sleep(duration / 2)
                    GPIO.output(pin, GPIO.LOW)
                    time.sleep(duration / 2)
                elif pattern == "pulse":
                    # Fade in and out
                    for i in range(10):
                        GPIO.output(pin, GPIO.HIGH)
                        time.sleep(duration / 20)
                        GPIO.output(pin, GPIO.LOW)
                        time.sleep(duration / 20)
                elif pattern == "solid":
                    GPIO.output(pin, GPIO.HIGH)
                    time.sleep(duration)
                    GPIO.output(pin, GPIO.LOW)
                else:
                    # Default blink
                    GPIO.output(pin, GPIO.HIGH)
                    time.sleep(duration / 2)
                    GPIO.output(pin, GPIO.LOW)
                    time.sleep(duration / 2)
                
                time.sleep(0.1)  # Small delay between repetitions
                
        except Exception as e:
            logger.error(f"Error executing LED pattern: {e}")
    
    def _execute_buzzer_pattern(self, frequency: int, duty_cycle: int, duration: float, repetitions: int):
        """Execute buzzer pattern"""
        if self.simulation_mode or not GPIO_AVAILABLE:
            logger.info(f"SIMULATION: Buzzer {frequency}Hz, {duty_cycle}% duty for {duration}s, {repetitions} times")
            return
        
        try:
            if self.pwm:
                for _ in range(repetitions):
                    self.pwm.ChangeFrequency(frequency)
                    # Duty is active-high PWM
                    self.pwm.ChangeDutyCycle(duty_cycle if self.buzzer_active_high else 0)
                    time.sleep(duration)
                    self.pwm.ChangeDutyCycle(0 if self.buzzer_active_high else duty_cycle)
                    time.sleep(0.1)
            else:
                # Fallback to simple on/off
                for _ in range(repetitions):
                    GPIO.output(self.buzzer_pin, GPIO.HIGH if self.buzzer_active_high else GPIO.LOW)
                    time.sleep(duration)
                    GPIO.output(self.buzzer_pin, GPIO.LOW if self.buzzer_active_high else GPIO.HIGH)
                    time.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"Error executing buzzer pattern: {e}")
    
    def _update_order_display(self, notification: Notification):
        """Update the order display with new order information"""
        try:
            # Fetch latest orders from server (with backoff/circuit-breaker)
            orders = self._fetch_undelivered_orders()
            if orders:
                # Fade out any orders that disappeared in this refresh window
                try:
                    old_list = list(self.orders_to_display)
                    old_by_id = {o.get('id'): o for o in old_list}
                    new_ids = {o.get('id') for o in orders}
                    removed_ids = [oid for oid in old_by_id.keys() if oid not in new_ids]
                    now_ts = time.time()
                    for oid in removed_ids:
                        if oid is None:
                            continue
                        if oid not in self.fading_orders:
                            self.fading_orders[oid] = {
                                'order': old_by_id.get(oid, {'id': oid}),
                                'started_at': now_ts,
                                'expires_at': now_ts + self.delivered_card_fade_seconds
                            }
                except Exception:
                    pass
                self.orders_to_display.clear()
                self.orders_to_display.extend(orders)
                logger.info(f"Updated display with {len(orders)} undelivered orders")
                self.last_orders_update_time = time.time()
        except Exception as e:
            logger.error(f"Error updating order display: {e}")
    
    def _fetch_undelivered_orders(self) -> List[Dict[str, Any]]:
        """Fetch undelivered orders from the server for this specific restaurant"""
        try:
            now = time.time()
            if now < self.fetch_backoff_until:
                # In backoff window: return cached orders
                return list(self.orders_to_display)
            # Construct API endpoint - use the correct endpoint from your app
            api_url = f"{self.server_url}/api/orders"
            params = {
                'restaurant_id': self.restaurant_id,
                # Use the working status filter that matches the API
                'status': 'new,pending,preparing,ready'
            }
            
            # Log the exact API call being made
            full_url = f"{api_url}?restaurant_id={self.restaurant_id}&status={params['status']}"
            logger.info(f"Fetching orders from: {full_url}")
            
            response = requests.get(api_url, params=params, timeout=5)
            response.raise_for_status()
            
            # The API returns a list directly, not a dictionary with 'orders' key
            orders = response.json()
            logger.info(f"API response: {len(orders) if isinstance(orders, list) else 'not a list'} orders received")
            
            # Ensure we have a list
            if isinstance(orders, list):
                # Success -> reset backoff
                self.fetch_backoff_seconds = 0
                self.fetch_backoff_until = 0
                # Filter out delivered locally for display/processing as active
                try:
                    filtered = [o for o in orders if str(o.get('status','')).lower() != 'delivered']
                except Exception:
                    filtered = orders
                try:
                    logger.info(f"Fetched {len(filtered)} active orders (post-filter) from {api_url}?restaurant_id={self.restaurant_id}")
                except Exception:
                    pass
                return filtered
            elif isinstance(orders, dict) and 'orders' in orders:
                self.fetch_backoff_seconds = 0
                self.fetch_backoff_until = 0
                try:
                    data_list = orders.get('orders', [])
                except Exception:
                    data_list = []
                try:
                    filtered = [o for o in data_list if str(o.get('status','')).lower() != 'delivered']
                except Exception:
                    filtered = data_list
                try:
                    logger.info(f"Fetched {len(filtered)} active orders (dict format, post-filter)")
                except Exception:
                    pass
                return filtered
            else:
                logger.warning(f"Unexpected response format: {type(orders)}")
                return []
            
        except Exception as e:
            logger.error(f"Error fetching orders for restaurant {self.restaurant_id}: {e}")
            # Exponential backoff with jitter up to 60s
            if self.fetch_backoff_seconds == 0:
                self.fetch_backoff_seconds = 2
            else:
                self.fetch_backoff_seconds = min(self.fetch_backoff_seconds * 2, 60)
            jitter = random.uniform(0, self.fetch_backoff_seconds / 2)
            self.fetch_backoff_until = time.time() + self.fetch_backoff_seconds + jitter
            # Return cached if available
            return list(self.orders_to_display)
    
    def _check_internet(self, host="8.8.8.8", port=53, timeout=3):
        """Check if the device has internet connectivity."""
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except Exception:
            return False

    def _orders_refresh_loop(self):
        """Background loop to periodically refresh undelivered orders for real-time updates and socket fallback."""
        logger.info("Orders refresh loop started")
        while self.running:
            try:
                orders = self._fetch_undelivered_orders()
                if orders is not None:
                    # Determine orders that disappeared (likely delivered) and start fading them out
                    try:
                        old_list = list(self.orders_to_display)
                        old_by_id = {o.get('id'): o for o in old_list}
                        new_ids = {o.get('id') for o in orders}
                        removed_ids = [oid for oid in old_by_id.keys() if oid not in new_ids]
                        now_ts = time.time()
                        for oid in removed_ids:
                            if oid is None:
                                continue
                            if oid not in self.fading_orders:
                                self.fading_orders[oid] = {
                                    'order': old_by_id.get(oid, {'id': oid}),
                                    'started_at': now_ts,
                                    'expires_at': now_ts + self.delivered_card_fade_seconds
                                }
                            # Notify delivered when order disappears from undelivered set
                            try:
                                self.notify(NotificationType.ORDER_DELIVERED, priority=2, metadata={'source': 'polling', 'order_id': oid})
                                # Delivery flash overlay
                                self.recent_deliveries.append({
                                    'order_id': oid,
                                    'started_at': now_ts,
                                    'expires_at': now_ts + self.delivered_flash_seconds
                                })
                            except Exception:
                                pass
                    except Exception:
                        pass
                    # Delta-based notifications for NEW and READY based on status transitions
                    try:
                        current_map = {o.get('id'): o for o in list(orders)}
                        prev_map = dict(self.prev_orders_by_id or {})
                        current_ids = set(current_map.keys())
                        prev_ids = set(prev_map.keys())
                        # New orders
                        for oid in current_ids - prev_ids:
                            if oid is None:
                                continue
                            try:
                                self.notify(NotificationType.NEW_ORDER, priority=3, metadata={'source': 'polling', 'order_id': oid})
                            except Exception:
                                pass
                        # Status transitions
                        for oid in current_ids & prev_ids:
                            try:
                                new_status = str(current_map.get(oid, {}).get('status', '')).lower()
                                old_status = str(prev_map.get(oid, {}).get('status', '')).lower()
                                if new_status != old_status and new_status == 'ready':
                                    self.notify(NotificationType.ORDER_READY, priority=4, metadata={'source': 'polling', 'order_id': oid})
                            except Exception:
                                pass
                        # Update snapshot
                        self.prev_orders_by_id = current_map
                    except Exception:
                        try:
                            self.prev_orders_by_id = {o.get('id'): o for o in list(orders)}
                        except Exception:
                            self.prev_orders_by_id = {}
                    # Replace current list to auto-hide delivered orders
                    self.orders_to_display.clear()
                    self.orders_to_display.extend(orders)
                    self.last_orders_update_time = time.time()
            except Exception as e:
                logger.warning(f"Orders refresh loop error: {e}")
            finally:
                try:
                    time.sleep(max(0.5, float(self.refresh_interval_seconds)))
                except Exception:
                    time.sleep(3.0)

    def _display_orders(self):
        """Display orders on the screen in grid mode"""
        if not DISPLAY_AVAILABLE:
            logger.info("Display not available, skipping display thread")
            return
        
        logger.info("Display thread: Starting pygame initialization...")
        try:
            pygame.init()
            logger.info("Display thread: Pygame initialized successfully")
            
            # Test display access before proceeding
            try:
                logger.info("Display thread: Testing display access...")
                info = pygame.display.Info()
                screen_width = info.current_w
                screen_height = info.current_h
                logger.info(f"Display thread: Display info - width: {screen_width}, height: {screen_height}")
                
                if screen_width <= 0 or screen_height <= 0:
                    logger.error("Display thread: No valid display detected, skipping display initialization")
                    return
            except Exception as e:
                logger.error(f"Display thread: Could not get display info: {e}")
                logger.error(f"Display thread: Traceback: {traceback.format_exc()}")
                screen_width = 1024
                screen_height = 768
            
            # Try to create display surface
            logger.info("Display thread: Attempting to create display surface...")
            display_created = False
            
            # Try fullscreen first
            try:
                self.display_surface = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
                logger.info("Display thread: Fullscreen mode successful")
                display_created = True
            except Exception as e:
                logger.warning(f"Display thread: Fullscreen mode failed: {e}")
                
                # Try windowed mode
                try:
                    self.display_surface = pygame.display.set_mode((screen_width, screen_height))
                    logger.info("Display thread: Windowed mode successful")
                    display_created = True
                except Exception as e2:
                    logger.warning(f"Display thread: Windowed mode failed: {e2}")
                    
                    # Try with smaller resolution as fallback
                    try:
                        fallback_width = min(1024, screen_width)
                        fallback_height = min(768, screen_height)
                        self.display_surface = pygame.display.set_mode((fallback_width, fallback_height))
                        logger.info(f"Display thread: Fallback mode successful ({fallback_width}x{fallback_height})")
                        screen_width, screen_height = fallback_width, fallback_height
                        display_created = True
                    except Exception as e3:
                        logger.error(f"Display thread: All display modes failed")
                        logger.error(f"Display thread: Fullscreen error: {e}")
                        logger.error(f"Display thread: Windowed error: {e2}")
                        logger.error(f"Display thread: Fallback error: {e3}")
                        logger.error(f"Display thread: Traceback: {traceback.format_exc()}")
                        return
            
            if not display_created:
                logger.error("Display thread: Failed to create any display surface")
                return
            
            pygame.display.set_caption("BlueSpace Restaurant - Kitchen Display")
            logger.info("Display thread: Display surface created successfully")
            
            # Test if we can actually render to the surface
            try:
                test_surface = pygame.Surface((100, 100))
                test_surface.fill((255, 0, 0))  # Red test surface
                self.display_surface.blit(test_surface, (0, 0))
                pygame.display.flip()
                logger.info("Display thread: Display rendering test successful")
            except Exception as render_error:
                logger.error(f"Display thread: Display rendering test failed: {render_error}")
                return
            
            try:
                base_w = max(640, screen_width)
                # Scale fonts relative to screen width to prevent overlap
                title_font = pygame.font.Font(None, max(48, int(base_w * 0.05)))
                order_font = pygame.font.Font(None, max(32, int(base_w * 0.036)))
                detail_font = pygame.font.Font(None, max(22, int(base_w * 0.026)))
                logger.info("Display thread: Fonts initialized successfully")
            except Exception as e:
                logger.warning(f"Display thread: Default font failed: {e}")
                try:
                    title_font = pygame.font.SysFont('arial', max(48, int(base_w * 0.05)))
                    order_font = pygame.font.SysFont('arial', max(32, int(base_w * 0.036)))
                    detail_font = pygame.font.SysFont('arial', max(22, int(base_w * 0.026)))
                    logger.info("Display thread: System fonts initialized successfully")
                except Exception as e2:
                    logger.error(f"Display thread: Could not initialize fonts: {e2}")
                    logger.error(f"Display thread: Traceback: {traceback.format_exc()}")
                    return
            BLACK = (0, 0, 0)
            WHITE = (255, 255, 255)
            ORANGE = (230, 126, 34)
            RED = (231, 76, 60)
            GREEN = (46, 204, 113)
            YELLOW = (241, 196, 15)
            
            logger.info("Display thread: Starting main display loop...")
            logger.info("Display thread: Display system fully initialized and ready!")
            while self.running:
                try:
                    self.internet_available = self._check_internet()
                    self.display_surface.fill(BLACK)
                    header_text = title_font.render(f"Restaurant #{self.restaurant_id} - Kitchen Orders", True, WHITE)
                    header_rect = header_text.get_rect(center=(screen_width // 2, 50))
                    self.display_surface.blit(header_text, header_rect)
                    
                    # Staleness indicator
                    age = 0
                    try:
                        if self.last_orders_update_time:
                            age = int(time.time() - self.last_orders_update_time)
                    except Exception:
                        age = 0
                    ts_color = WHITE
                    if age >= self.stale_red_seconds:
                        ts_color = RED
                    elif age >= self.stale_yellow_seconds:
                        ts_color = YELLOW
                    timestamp_text = detail_font.render(
                        f"Last Updated: {datetime.now().strftime('%H:%M:%S')} (age {age}s)", 
                        True, ts_color
                    )
                    timestamp_rect = timestamp_text.get_rect(center=(screen_width // 2, 100))
                    self.display_surface.blit(timestamp_text, timestamp_rect)
                    
                    # Pending banner
                    pending_count = len(self.orders_to_display)
                    banner_color = ORANGE if pending_count > 0 else GREEN
                    pending_text = order_font.render(f"Pending Orders: {pending_count}", True, banner_color)
                    pending_rect = pending_text.get_rect(center=(screen_width // 2, 140))
                    self.display_surface.blit(pending_text, pending_rect)
                    
                    if not self.internet_available:
                        no_internet_text = order_font.render("No Internet Connection", True, RED)
                        no_internet_rect = no_internet_text.get_rect(center=(screen_width // 2, screen_height // 2))
                        self.display_surface.blit(no_internet_text, no_internet_rect)
                    else:
                        self._render_orders_grid(screen_width, screen_height, order_font, detail_font, 
                               BLACK, WHITE, ORANGE, RED, GREEN, YELLOW)
                    
                    pygame.display.flip()
                    
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            self.running = False
                        elif event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_ESCAPE:
                                self.running = False
                    
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Display thread: Error in main loop: {e}")
                    logger.error(f"Display thread: Traceback: {traceback.format_exc()}")
                    time.sleep(1.0)  # Wait before retrying
                    continue
        except Exception as e:
            logger.error(f"Display thread: Fatal error: {e}")
            logger.error(f"Display thread: Traceback: {traceback.format_exc()}")
        finally:
            try:
                if pygame.get_init():
                    pygame.quit()
                    logger.info("Display thread: Pygame quit successfully")
            except Exception as cleanup_error:
                logger.error(f"Display thread: Error during cleanup: {cleanup_error}")
            logger.info("Display thread: Exiting")
    
    def _draw_order_card(self, order: Dict[str, Any], x: int, y: int, width: int, height: int, order_font, detail_font, fade_alpha: int = 255):
        """Draw an order card at a specific position and size on the display (for grid layout).
        fade_alpha applies an overall opacity to enable fade-out animations for delivered cards."""
        WHITE = (255, 255, 255)
        ORANGE = (230, 126, 34)
        RED = (231, 76, 60)
        GREEN = (46, 204, 113)
        YELLOW = (241, 196, 15)
        GRAY = (128, 128, 128)
        BLACK = (0, 0, 0)
        # Draw to an offscreen surface to control alpha
        try:
            card_surface = pygame.Surface((max(1, width), max(1, height)), pygame.SRCALPHA)
        except Exception:
            card_surface = self.display_surface
        # Card background with rounded border and internal padding
        padding = 14
        pygame.draw.rect(card_surface, WHITE, (0, 0, width, height))
        pygame.draw.rect(card_surface, ORANGE, (0, 0, width, height), 5, border_radius=10)
        order_id = order.get('id', 'N/A')
        status = str(order.get('status', 'unknown')).upper()
        order_type = str(order.get('order_type', 'DINE_IN')).upper()
        # Status badge color similar to web
        if status in ['NEW', 'PENDING']:
            status_color = YELLOW
        elif status == 'READY':
            status_color = GREEN
        else:
            status_color = GRAY
        header_text = order_font.render(f"Order #{order_id}", True, BLACK)
        card_surface.blit(header_text, (padding, padding))
        # Draw a rounded status badge on the top right
        try:
            badge_text = detail_font.render(status, True, WHITE)
            badge_w, badge_h = badge_text.get_size()
            pad_x, pad_y = 14, 6
            rect_w = badge_w + 2 * pad_x
            rect_h = badge_h + 2 * pad_y
            rect_x = width - rect_w - padding
            rect_y = padding
            pygame.draw.rect(card_surface, status_color, (rect_x, rect_y, rect_w, rect_h), border_radius=8)
            card_surface.blit(badge_text, (rect_x + pad_x, rect_y + pad_y))
        except Exception:
            pass
        # Order type line (icon-like text)
        type_label = 'DINE-IN' if order_type in ['DINE_IN', 'DINEIN', 'DINEINN', 'DINE'] else ('DELIVERY' if order_type == 'DELIVERY' else order_type)
        type_text = detail_font.render(type_label, True, ORANGE)
        card_surface.blit(type_text, (padding, padding + 40))
        customer_name = order.get('customer_name', 'Walk-in Customer')
        customer_phone = order.get('customer_phone', 'N/A')
        customer_text = detail_font.render(f"Customer: {customer_name}", True, BLACK)
        card_surface.blit(customer_text, (padding, 110))
        phone_text = detail_font.render(f"Phone: {customer_phone}", True, BLACK)
        card_surface.blit(phone_text, (padding, 140))
        items = order.get('items', [])
        if isinstance(items, str):
            try:
                items = json.loads(items)
            except:
                items = []
        y_offset = 96
        # Items list (like web cards; omit prices for compactness on small tiles)
        for i, item in enumerate(items[:self.display_max_items]):
            if isinstance(item, dict):
                name = item.get('name', 'Unknown Item')
                quantity = item.get('quantity', 1)
            else:
                name = str(item)
                quantity = 1
            item_text = detail_font.render(f"{quantity}x {name}", True, BLACK)
            card_surface.blit(item_text, (padding, y_offset))
            y_offset += 26
        if len(items) > self.display_max_items:
            remaining = len(items) - self.display_max_items
            more_text = detail_font.render(f"... and {remaining} more", True, GRAY)
            card_surface.blit(more_text, (padding, y_offset))
            y_offset += 24
        special_instructions = order.get('special_instructions', '')
        if special_instructions:
            instructions_text = detail_font.render(f"Special Instructions: {special_instructions}", True, RED)
            card_surface.blit(instructions_text, (padding, y_offset))
            y_offset += 28
        # Footer row with total and time
        total = float(order.get('total_amount', 0) or 0)
        # Note: This is hardcoded to $ for hardware display - consider making configurable
        total_text = detail_font.render(f"Total: ${total:.2f}", True, ORANGE)
        card_surface.blit(total_text, (padding, height - 44))
        created_at = order.get('created_at', '')
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                time_str = dt.strftime('%H:%M:%S')
                time_text = detail_font.render(f"{time_str}", True, GRAY)
                # Right align time in footer
                tw, th = time_text.get_size()
                card_surface.blit(time_text, (width - tw - 16, height - 44))
            except:
                pass
        # Blit card with fade alpha
        try:
            if card_surface is not self.display_surface:
                card_surface.set_alpha(max(0, min(255, int(fade_alpha))))
                self.display_surface.blit(card_surface, (x, y))
        except Exception:
            self.display_surface.blit(card_surface, (x, y))
    
    def _render_orders_grid(self, screen_width: int, screen_height: int, order_font, detail_font, 
                           BLACK, WHITE, ORANGE, RED, GREEN, YELLOW):
        """Render the orders in a grid layout on the display."""
        if not self.orders_to_display:
            # Show "No Orders" message
            no_orders_text = order_font.render("No Active Orders", True, WHITE)
            no_orders_rect = no_orders_text.get_rect(center=(screen_width // 2, screen_height // 2))
            self.display_surface.blit(no_orders_text, no_orders_rect)
            return
        
        # Grid layout parameters
        margin = 20
        card_width = 300
        card_height = 200
        cards_per_row = max(1, (screen_width - 2 * margin) // (card_width + margin))
        
        # Calculate starting position to center the grid
        total_grid_width = min(len(self.orders_to_display), cards_per_row) * card_width + (min(len(self.orders_to_display), cards_per_row) - 1) * margin
        start_x = (screen_width - total_grid_width) // 2 + margin
        
        # Start Y position (below header)
        start_y = 180
        
        # Render each order
        for i, order in enumerate(self.orders_to_display):
            if i >= self.display_max_orders:
                break
                
            row = i // cards_per_row
            col = i % cards_per_row
            
            x = start_x + col * (card_width + margin)
            y = start_y + row * (card_height + margin)
            
            # Check if this order is fading out
            fade_alpha = 255
            if order.get('id') in self.fading_orders:
                fade_info = self.fading_orders[order.get('id')]
                elapsed = time.time() - fade_info['started_at']
                fade_alpha = max(0, int(255 * (1 - elapsed / self.delivered_card_fade_seconds)))
                
                # Remove expired fade entries
                if elapsed >= self.delivered_card_fade_seconds:
                    del self.fading_orders[order.get('id')]
            
            # Draw the order card
            self._draw_order_card(order, x, y, card_width, card_height, 
                                order_font, detail_font, fade_alpha)
    
    def _draw_slide_indicator(self, current_slide: int, total_slides: int, screen_width: int, screen_height: int):
        """Disabled: no sliding indicator in full grid mode."""
        return
    
    def cleanup(self):
        """Clean up hardware resources"""
        self.running = False
        # Idempotent cleanup
        if getattr(self, '_cleaned', False):
            return
        self._cleaned = True
        
        # Avoid joining threads in gevent signal context; just mark running False
        
        # Signal background loops/threads to stop
        try:
            if getattr(self, '_shutdown_event', None):
                self._shutdown_event.set()
        except Exception:
            pass
        
        # Clean up GPIO
        if not self.simulation_mode and GPIO_AVAILABLE:
            try:
                if self.pwm:
                    self.pwm.stop()
                
                # Turn off all LEDs
                for pin in self.led_pins.values():
                    GPIO.output(pin, GPIO.LOW)
                
                # Turn off buzzer
                if self.buzzer_pin:
                    GPIO.output(self.buzzer_pin, GPIO.LOW)
                
                GPIO.cleanup()
                logger.info("GPIO cleanup completed")
                
            except Exception as e:
                logger.error(f"Error during GPIO cleanup: {e}")
        
        # Disconnect Socket.IO client
        try:
            if self.sio:
                try:
                    self.sio.disconnect()
                except Exception:
                    pass
                self.sio = None
        except Exception:
            pass
        
        # Stop health server without blocking the event loop
        try:
            if self.health_server:
                def _shutdown_server(server):
                    try:
                        server.shutdown()
                        server.server_close()
                    except Exception as e:
                        logger.warning(f"Error shutting down health server: {e}")
                try:
                    threading.Thread(target=_shutdown_server, args=(self.health_server,), daemon=True).start()
                except Exception as e:
                    logger.warning(f"Failed to spawn health server shutdown thread: {e}")
                    # Fallback to direct shutdown if thread cannot be spawned
                    try:
                        _shutdown_server(self.health_server)
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"Error shutting down health server: {e}")

        logger.info("Hardware notifier cleanup completed")

    # --- Socket.IO Integration (push updates, no polling dependency) ---
    def _start_socket(self):
        try:
            import socketio
        except Exception as e:
            logger.warning(f"python-socketio not available: {e}")
            return

        # Allow turning on verbose logs via env SIO_DEBUG=1
        try:
            sio_debug = str(os.environ.get('SIO_DEBUG', '0')).strip() in ('1','true','True')
        except Exception:
            sio_debug = False
        self.sio = socketio.Client(reconnection=True, reconnection_attempts=0, logger=sio_debug, engineio_logger=sio_debug)

        @self.sio.event
        def connect():
            try:
                logger.info("Socket.IO connected; joining order room")
                self.sio.emit('join_orders', { 'user_id': self.restaurant_id })
            except Exception as e:
                logger.warning(f"Error on connect handler: {e}")

        @self.sio.on('order_update')
        def on_order_update(data):
            try:
                # Map order status to notification type
                status = str(data.get('status', '')).lower()
                ntype = None
                priority = 1
                if status in ['new', 'pending']:
                    ntype = NotificationType.NEW_ORDER
                    priority = 3
                elif status == 'ready':
                    ntype = NotificationType.ORDER_READY
                    priority = 4
                elif status == 'delivered':
                    ntype = NotificationType.ORDER_DELIVERED
                    priority = 2
                elif status in ['paid', 'payment_confirmed']:
                    ntype = NotificationType.PAYMENT_RECEIVED
                    priority = 3
                if ntype:
                    self.notify(ntype, priority=priority, metadata={'source': 'socketio', 'order_id': data.get('id')})
                    # Update display list:
                    # - For NEW/PENDING/READY: refresh from server
                    # - For DELIVERED: remove locally and refresh from server to be safe
                    try:
                        if ntype is NotificationType.ORDER_DELIVERED:
                            oid = data.get('id')
                            if oid is not None:
                                # Start per-card fade if we have the order present
                                try:
                                    current = list(self.orders_to_display)
                                    target = None
                                    for o in current:
                                        if o.get('id') == oid:
                                            target = o
                                            break
                                    if target is not None:
                                        now_ts = time.time()
                                        self.fading_orders[oid] = {
                                            'order': target,
                                            'started_at': now_ts,
                                            'expires_at': now_ts + self.delivered_card_fade_seconds
                                        }
                                        # Remove from active list; it will continue to render via fade map until expired
                                    filtered = [o for o in current if o.get('id') != oid]
                                    self.orders_to_display.clear()
                                    self.orders_to_display.extend(filtered)
                                except Exception:
                                    pass
                                # Queue a brief delivery flash overlay
                                now_ts = time.time()
                                try:
                                    self.recent_deliveries.append({
                                        'order_id': oid,
                                        'started_at': now_ts,
                                        'expires_at': now_ts + self.delivered_flash_seconds
                                    })
                                except Exception:
                                    pass
                        # Best-effort refresh; if fade is in progress, keep it
                        orders = self._fetch_undelivered_orders()
                        if orders is not None:
                            # Remove any orders that are fading from the fresh list, so they do not pop back
                            fading_ids = set(self.fading_orders.keys())
                            filtered = [o for o in orders if o.get('id') not in fading_ids]
                            self.orders_to_display.clear()
                            self.orders_to_display.extend(filtered)
                            self.last_orders_update_time = time.time()
                    except Exception:
                        pass
            except Exception as e:
                logger.warning(f"order_update handler error: {e}")

        @self.sio.event
        def disconnect():
            logger.info("Socket.IO disconnected")

        @self.sio.event
        def connect_error(data=None):
            try:
                logger.warning(f"Socket.IO connect_error: {data}")
            except Exception:
                logger.warning("Socket.IO connect_error")

        @self.sio.event
        def reconnect():
            logger.info("Socket.IO reconnected")

        @self.sio.event
        def reconnect_attempt(number=None):
            try:
                logger.info(f"Socket.IO reconnect attempt: {number}")
            except Exception:
                logger.info("Socket.IO reconnect attempt")

        def _socket_thread():
            while not (self._shutdown_event.is_set() if self._shutdown_event else False):
                try:
                    try:
                        logger.info(f"Socket.IO: attempting connect to {self.server_url}")
                    except Exception:
                        pass
                    self.sio.connect(self.server_url, transports=['websocket', 'polling'], wait_timeout=10, socketio_path='socket.io')
                    self.sio.wait()
                except Exception as e:
                    # Break early if shutdown requested
                    if self._shutdown_event and self._shutdown_event.is_set():
                        break
                    logger.warning(f"Socket.IO connect/wait error: {e}")
                    time.sleep(3)

        threading.Thread(target=_socket_thread, daemon=True, name="HardwareNotifier-SocketIO").start()

    # --- Health Server ---
    def _current_status(self) -> Dict[str, Any]:
        try:
            qsize = 0
            with self.notification_queue.mutex:
                qsize = len(self.notification_queue.queue)
        except Exception:
            qsize = -1
        return {
            'running': self.running,
            'processing_thread_alive': bool(self.processing_thread and self.processing_thread.is_alive()),
            'display_thread_alive': bool(self.display_thread and self.display_thread.is_alive()) if self.display_thread else False,
            'internet_available': self.internet_available,
            'queue_size': qsize,
            'fetch_backoff_seconds': self.fetch_backoff_seconds,
            'fetch_backoff_until': self.fetch_backoff_until,
            'server_url': self.server_url,
            'restaurant_id': self.restaurant_id,
            'simulation_mode': self.simulation_mode,
            'gpio_available': GPIO_AVAILABLE,
            'display_available': DISPLAY_AVAILABLE,
        }

    def _start_health_server(self):
        # Use env-provided port if set; otherwise let OS choose an ephemeral port to avoid clashes
        port = int(os.environ.get('HEALTH_PORT', '0'))
        notifier = self

        class ThreadingHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
            daemon_threads = True
            timeout = 2.0

        class HealthHandler(BaseHTTPRequestHandler):
            # Use HTTP/1.0 to simplify response semantics (no keep-alive)
            protocol_version = 'HTTP/1.0'
            def do_GET(self):
                try:
                    try:
                        logger.info(f"Health request: {self.path}")
                    except Exception:
                        pass

                    if self.path == '/health':
                        status = notifier._current_status()
                        body = json.dumps(status).encode('utf-8')
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('Content-Length', str(len(body)))
                        self.end_headers()
                        self.wfile.write(body)
                        try:
                            self.wfile.flush()
                            try:
                                self.connection.shutdown(socket.SHUT_WR)
                            except Exception:
                                pass
                        except Exception:
                            pass
                    else:
                        body = b'OK'
                        self.send_response(200)
                        self.send_header('Content-Type', 'text/plain; charset=utf-8')
                        self.send_header('Content-Length', str(len(body)))
                        self.end_headers()
                        self.wfile.write(body)
                        try:
                            self.wfile.flush()
                            try:
                                self.connection.shutdown(socket.SHUT_WR)
                            except Exception:
                                pass
                        except Exception:
                            pass
                except Exception as e:
                    try:
                        err = f'error: {e}'.encode('utf-8')
                        self.send_response(500)
                        self.send_header('Content-Type', 'text/plain; charset=utf-8')
                        self.send_header('Content-Length', str(len(err)))
                        self.end_headers()
                        self.wfile.write(err)
                    except Exception:
                        pass
            def log_message(self, format, *args):
                # Suppress default access log to keep logs clean
                return

        self.health_server = ThreadingHTTPServer(('0.0.0.0', port), HealthHandler)

        def _serve():
            try:
                logger.info(f"Health server listening on 0.0.0.0:{port}")
                self.health_server.serve_forever(poll_interval=0.5)
            except Exception as e:
                logger.warning(f"Health server error: {e}")

        self.health_thread = threading.Thread(target=_serve, daemon=True, name="HardwareNotifier-Health")
        self.health_thread.start()

    def _watchdog_loop(self):
        """Ensure processing/display threads remain alive; restart on failure."""
        while True:
            try:
                if self.running:
                    # Health server
                    try:
                        health_ok = bool(self.health_thread and self.health_thread.is_alive())
                    except Exception:
                        health_ok = False
                    if not health_ok:
                        try:
                            self._start_health_server()
                        except Exception as e:
                            logger.warning(f"Failed to (re)start health server: {e}")
                    # Processing thread
                    if not (self.processing_thread and self.processing_thread.is_alive()):
                        logger.warning("Processing thread is not alive; restarting...")
                        try:
                            self.processing_thread = threading.Thread(target=self._process_notifications, daemon=True, name="HardwareNotifier-Processing")
                            self.processing_thread.start()
                        except Exception as e:
                            logger.error(f"Failed to restart processing thread: {e}")
                    # Orders refresh thread
                    if not (self.refresh_thread and self.refresh_thread.is_alive()):
                        try:
                            self.refresh_thread = threading.Thread(target=self._orders_refresh_loop, daemon=True, name="HardwareNotifier-OrdersRefresh")
                            self.refresh_thread.start()
                            logger.info("Orders refresh thread restarted")
                        except Exception as e:
                            logger.error(f"Failed to restart orders refresh thread: {e}")
                    # Display thread
                    if DISPLAY_AVAILABLE and not self.simulation_mode:
                        if not (self.display_thread and self.display_thread.is_alive()):
                            try:
                                logger.warning("Display thread is not alive; restarting...")
                                self.display_thread = threading.Thread(target=self._display_orders, daemon=True, name="HardwareNotifier-Display")
                                self.display_thread.start()
                                # Wait a moment to confirm restart
                                time.sleep(0.5)
                                if self.display_thread.is_alive():
                                    logger.info("Display thread restarted successfully")
                                else:
                                    logger.error("Display thread restart failed")
                            except Exception as e:
                                logger.error(f"Failed to restart display thread: {e}")
                                logger.error(f"Display thread restart traceback: {traceback.format_exc()}")
                time.sleep(2.0)
            except Exception as e:
                logger.warning(f"Watchdog loop error: {e}")
                time.sleep(5.0)

# Singleton instance
_hardware_notifier_instance = None

def get_hardware_notifier(simulation_mode: bool = False) -> HardwareNotifier:
    """Get the singleton hardware notifier instance"""
    global _hardware_notifier_instance
    
    if _hardware_notifier_instance is None:
        _hardware_notifier_instance = HardwareNotifier(simulation_mode=simulation_mode)
    
    return _hardware_notifier_instance

def cleanup_hardware_notifier():
    """Clean up the hardware notifier instance"""
    global _hardware_notifier_instance
    
    if _hardware_notifier_instance:
        try:
            _hardware_notifier_instance.cleanup()
        except Exception as e:
            logger.error(f"Error during hardware notifier cleanup: {e}")
        finally:
            _hardware_notifier_instance = None

def _signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, cleaning up hardware notifier...")
    cleanup_hardware_notifier()

# Register signal handlers and cleanup function
signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGINT, _signal_handler)
atexit.register(cleanup_hardware_notifier)

# Test function
def test_hardware_notifier():
    """Test the hardware notifier functionality"""
    print("Testing Hardware Notifier...")
    
    notifier = get_hardware_notifier(simulation_mode=True)
    
    # Test different notification types
    test_notifications = [
        (NotificationType.NEW_ORDER, 3),
        (NotificationType.ORDER_READY, 4),
        (NotificationType.PAYMENT_RECEIVED, 2),
        (NotificationType.ERROR, 5),
    ]
    
    for notification_type, priority in test_notifications:
        print(f"Testing {notification_type.value}...")
        success = notifier.notify(notification_type, priority=priority)
        print(f"  Success: {success}")
        time.sleep(2)
    
    print("Test completed!")
    cleanup_hardware_notifier()

if __name__ == "__main__":
    # Lightweight CLI to run the notifier on Raspberry Pi or simulate on dev
    try:
        import argparse
    except Exception:
        argparse = None
    if argparse is None:
        test_hardware_notifier()
        sys.exit(0)
    parser = argparse.ArgumentParser(description="Run BlueSpace Hardware Notifier")
    parser.add_argument("--server-url", default=os.environ.get("SERVER_URL", CFG_SERVER_URL), help="Base server URL, e.g., https://bluespace-restaurants.onrender.com")
    parser.add_argument("--restaurant-id", type=int, default=int(os.environ.get("RESTAURANT_ID", CFG_RESTAURANT_ID)), help="Restaurant ID to monitor")
    parser.add_argument("--simulate", action="store_true", help="Force simulation mode (no GPIO/display)")
    parser.add_argument("--test", action="store_true", help="Run hardware test")
    args = parser.parse_args()
    
    if args.test:
        # Run hardware test
        test_hardware_notifier()
        sys.exit(0)
    
    # Override config values at runtime
    try:
        notifier = get_hardware_notifier(simulation_mode=bool(args.simulate))
        notifier.server_url = str(args.server_url).rstrip("/")
        notifier.restaurant_id = int(args.restaurant_id)
        logger.info(f"Starting notifier for restaurant_id={notifier.restaurant_id} url={notifier.server_url}")
        # Keep running until interrupted
        while notifier.running:
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup_hardware_notifier()