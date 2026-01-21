#!/usr/bin/env python3
"""
Hardware Notifier Web Interface
Provides a web-based interface for monitoring and controlling the hardware notifier

This interface allows restaurant staff to:
- Monitor hardware status
- Test notifications
- View order display
- Configure settings
- View logs
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_socketio import SocketIO, emit
import json
import os
import time
import threading
from datetime import datetime
import logging

# Import the hardware notifier
from hardware_notifier import get_hardware_notifier, NotificationType

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'hardware-notifier-secret-key-2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Get hardware notifier instance
hardware_notifier = get_hardware_notifier(simulation_mode=False)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HardwareStatus:
    """Class to track hardware status"""
    def __init__(self):
        self.gpio_available = False
        self.display_available = False
        self.network_connected = False
        self.last_update = datetime.now()
        self.active_notifications = []
        self.system_uptime = time.time()
        
        # Check hardware availability
        self._check_hardware()
    
    def _check_hardware(self):
        """Check hardware availability"""
        try:
            import RPi.GPIO as GPIO
            self.gpio_available = True
        except ImportError:
            self.gpio_available = False
        
        try:
            import pygame
            pygame.init()
            info = pygame.display.Info()
            self.display_available = info.current_w > 0 and info.current_h > 0
            pygame.quit()
        except:
            self.display_available = False
    
    def get_status(self):
        """Get current status"""
        return {
            'gpio_available': self.gpio_available,
            'display_available': self.display_available,
            'network_connected': self.network_connected,
            'last_update': self.last_update.isoformat(),
            'uptime': time.time() - self.system_uptime,
            'active_notifications': len(self.active_notifications)
        }

# Global status tracker
status = HardwareStatus()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('hardware_dashboard.html')

@app.route('/api/status')
def get_status():
    """Get hardware status"""
    return jsonify(status.get_status())

@app.route('/api/test-notification', methods=['POST'])
def test_notification():
    """Test a notification"""
    try:
        data = request.get_json()
        notification_type = data.get('type', 'NEW_ORDER')
        
        # Map string to NotificationType enum
        type_mapping = {
            'NEW_ORDER': NotificationType.NEW_ORDER,
            'ORDER_READY': NotificationType.ORDER_READY,
            'ORDER_DELIVERED': NotificationType.ORDER_DELIVERED,
            'PAYMENT_RECEIVED': NotificationType.PAYMENT_RECEIVED,
            'ERROR': NotificationType.ERROR,
            'WARNING': NotificationType.WARNING,
            'INFO': NotificationType.INFO
        }
        
        notification_type_enum = type_mapping.get(notification_type, NotificationType.INFO)
        priority = data.get('priority', 1)
        
        # Send notification
        success = hardware_notifier.notify(notification_type_enum, priority=priority)
        
        if success:
            return jsonify({'success': True, 'message': f'Test notification sent: {notification_type}'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send notification'})
            
    except Exception as e:
        logger.error(f"Error testing notification: {e}")
        return jsonify({'success': False, 'message': str(e)})

def broadcast_orders_update():
    """Broadcast the latest undelivered orders to all connected clients for this specific restaurant."""
    try:
        orders = hardware_notifier._fetch_undelivered_orders()
        socketio.emit('orders_update', {
            'restaurant_id': RESTAURANT_ID,
            'orders': orders
        })
    except Exception as e:
        logger.error(f"Error broadcasting orders update for restaurant {RESTAURANT_ID}: {e}")

# Example: Call this function after any order change (new, update, delivered)
# You should call broadcast_orders_update() in your order management logic after changes.

# For demonstration, add a test endpoint to trigger it manually:
@app.route('/api/trigger-orders-update', methods=['POST'])
def trigger_orders_update():
    broadcast_orders_update()
    return jsonify({'success': True, 'message': f'Orders update broadcasted for restaurant {RESTAURANT_ID}'})

@app.route('/api/orders')
def get_orders():
    """Get current orders for display for this specific restaurant"""
    try:
        orders = hardware_notifier._fetch_undelivered_orders()
        return jsonify({
            'success': True, 
            'restaurant_id': RESTAURANT_ID,
            'orders': orders
        })
    except Exception as e:
        logger.error(f"Error fetching orders for restaurant {RESTAURANT_ID}: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/logs')
def get_logs():
    """Get recent logs"""
    try:
        log_file = 'hardware_notifier.log'
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()
                # Return last 50 lines
                recent_logs = lines[-50:] if len(lines) > 50 else lines
                return jsonify({'success': True, 'logs': recent_logs})
        else:
            return jsonify({'success': True, 'logs': ['No log file found']})
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/config')
def get_config():
    """Get current configuration"""
    try:
        from config import NOTIFICATION_CONFIG, HARDWARE_CONFIG
        return jsonify({
            'success': True,
            'notification_config': NOTIFICATION_CONFIG,
            'hardware_config': HARDWARE_CONFIG
        })
    except Exception as e:
        logger.error(f"Error reading config: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/restart', methods=['POST'])
def restart_service():
    """Restart the hardware notifier service"""
    try:
        # This would typically restart the systemd service
        # For now, we'll just reinitialize the hardware notifier
        global hardware_notifier
        hardware_notifier.cleanup()
        hardware_notifier = get_hardware_notifier(simulation_mode=False)
        
        return jsonify({'success': True, 'message': 'Service restarted successfully'})
    except Exception as e:
        logger.error(f"Error restarting service: {e}")
        return jsonify({'success': False, 'message': str(e)})

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected to hardware interface')
    emit('status_update', status.get_status())

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected from hardware interface')

@socketio.on('request_status')
def handle_status_request():
    """Handle status request"""
    emit('status_update', status.get_status())

def broadcast_status():
    """Broadcast status updates to connected clients"""
    while True:
        try:
            socketio.emit('status_update', status.get_status())
            time.sleep(5)  # Update every 5 seconds
        except Exception as e:
            logger.error(f"Error broadcasting status: {e}")

# Start status broadcasting thread
status_thread = threading.Thread(target=broadcast_status, daemon=True)
status_thread.start()

if __name__ == '__main__':
    print("Starting Hardware Notifier Web Interface...")
    print("Access the interface at: http://localhost:5001")
    socketio.run(app, host='0.0.0.0', port=5001, debug=False) 