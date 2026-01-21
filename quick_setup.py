#!/usr/bin/env python3
"""
Quick Setup Script for BlueSpace Restaurant Hardware Notifier

This utility provisions a Raspberry Pi (Debian-based) environment for the
BlueSpace Restaurant Hardware Notifier. It installs system and Python
dependencies, writes GPIO configuration and a test utility, creates a startup
shell script and a systemd service for autostart, and generates a lightweight
monitoring script for diagnostics.

Outputs created alongside this script:
- gpio_config.json — BCM pin configuration used by the notifier and tests
- test_gpio.py — quick GPIO exerciser based on the configuration file
- start_hardware_notifier.sh — startup wrapper that sets env vars and runs the app
- bluespace-hardware-notifier.service — systemd unit for autostart
- monitor_hardware.py — health checks for service, GPIO, display, and network

Intended platform: Raspberry Pi OS or compatible Debian with systemd. Running on
non-Linux platforms will not support GPIO/service features.
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path

def run_command(command, description=""):
    """Run a shell command and handle errors.

    Parameters:
        command (str): The exact shell command to execute.
        description (str): Optional human-readable label for logging.

    Returns:
        Optional[str]: Captured stdout on success; None on failure.
    """
    print(f"Running: {description or command}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description or command} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"✗ Error running '{command}': {e}")
        print(f"Error output: {e.stderr}")
        return None

def install_essential_packages():
    """Install essential system and Python packages required by the notifier.

    Uses `apt` for system libraries and headers, and `pip3` for Python
    dependencies including GPIO, Flask, SQLAlchemy, Pygame, and utilities.
    """
    print("\n=== Installing Essential Packages ===")
    
    # Install system dependencies
    essential_packages = [
        "python3-pip",
        "python3-dev",
        "libatlas-base-dev",
        "libopenjp2-7-dev",
        "libtiff5-dev",
        "libjpeg-dev",
        "libfreetype6-dev",
        "liblcms2-dev",
        "libwebp-dev",
        "libharfbuzz-dev",
        "libfribidi-dev",
        "libxcb1-dev",
        "libxrandr-dev",
        "libasound2-dev",
        "libpulse-dev",
        "libvorbis-dev",
        "libflac-dev",
        "libmodplug-dev",
        "libsmpeg-dev",
        "libsdl2-dev",
        "libsdl2-image-dev",
        "libsdl2-mixer-dev",
        "libsdl2-ttf-dev",
        "libportmidi-dev",
    ]
    
    for package in essential_packages:
        run_command(f"sudo apt install -y {package}", f"Install {package}")
    
    # Install Python packages
    python_packages = [
        "RPi.GPIO",
        "Pillow",
        "pygame",
        "requests",
        "flask",
        "flask-socketio",
        "flask-sqlalchemy",
        "flask-login",
        "flask-wtf",
        "flask-mail",
        "flask-migrate",
        "gevent",
        "gevent-websocket",
        "qrcode",
        "itsdangerous",
        "werkzeug",
        "sqlalchemy",
        "alembic",
        "wtforms",
        "email-validator",
    ]
    
    for package in python_packages:
        run_command(f"pip3 install {package}", f"Install Python package {package}")

def configure_gpio():
    """Write GPIO configuration and create a GPIO test script.

    Creates `gpio_config.json` with default BCM pin assignments and generates
    `test_gpio.py` which toggles each configured pin for verification.
    """
    print("\n=== Configuring GPIO Pins ===")
    
    # Create GPIO configuration
    gpio_config = {
        "DINE_IN_LED_PIN": 17,      # GPIO17
        "DELIVERY_LED_PIN": 27,     # GPIO27
        "BUZZER_PIN": 22,           # GPIO22
        "STATUS_LED_PIN": 18,       # GPIO18 (optional status LED)
    }
    
    # Save GPIO configuration
    with open('gpio_config.json', 'w') as f:
        json.dump(gpio_config, f, indent=2)
    
    print("✓ GPIO configuration saved to gpio_config.json")
    
    # Create GPIO test script
    gpio_test_script = '''#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
import json

def test_gpio():
    """Test GPIO pins"""
    try:
        # Load configuration
        with open('gpio_config.json', 'r') as f:
            config = json.load(f)
        
        # Set up GPIO
        GPIO.setmode(GPIO.BCM)
        
        # Test each pin
        for pin_name, pin_number in config.items():
            print(f"Testing {pin_name} (GPIO{pin_number})...")
            GPIO.setup(pin_number, GPIO.OUT)
            
            # Turn on
            GPIO.output(pin_number, GPIO.HIGH)
            time.sleep(1)
            
            # Turn off
            GPIO.output(pin_number, GPIO.LOW)
            time.sleep(0.5)
        
        GPIO.cleanup()
        print("✓ GPIO test completed successfully")
        
    except Exception as e:
        print(f"✗ GPIO test failed: {e}")
        GPIO.cleanup()

if __name__ == "__main__":
    test_gpio()
'''
    
    with open('test_gpio.py', 'w') as f:
        f.write(gpio_test_script)
    
    run_command("chmod +x test_gpio.py", "Make GPIO test script executable")
    print("✓ GPIO test script created")

def create_startup_script():
    """Create the startup shell script and a systemd unit template.

    Writes `start_hardware_notifier.sh` that sets environment variables and
    launches `hardware_notifier.py`, auto-restarting on exit. Also writes the
    `bluespace-hardware-notifier.service` unit file to be installed to
    `/etc/systemd/system/` for autostart.
    """
    print("\n=== Creating Startup Script ===")
    
    startup_script = '''#!/bin/bash
# BlueSpace Restaurant Hardware Notifier Startup Script

# Change to the application directory
cd /home/pi/BlueSpace-Restaurants

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set environment variables
export SIMULATION_MODE=false
export FLASK_ENV=production
export FLASK_APP=app.py

# Start the hardware notifier
echo "Starting BlueSpace Restaurant Hardware Notifier..."
python3 hardware_notifier.py

# If the script exits, restart it after a delay
echo "Hardware notifier stopped. Restarting in 5 seconds..."
sleep 5
exec "$0"
'''
    
    with open('start_hardware_notifier.sh', 'w') as f:
        f.write(startup_script)
    
    run_command("chmod +x start_hardware_notifier.sh", "Make startup script executable")
    
    # Create systemd service
    service_content = '''[Unit]
Description=BlueSpace Restaurant Hardware Notifier
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/BlueSpace-Restaurants
ExecStart=/home/pi/BlueSpace-Restaurants/start_hardware_notifier.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
'''
    
    with open('bluespace-hardware-notifier.service', 'w') as f:
        f.write(service_content)
    
    print("✓ Startup script and systemd service created")

def configure_autostart():
    """Install and enable the systemd unit for autostart.

    Copies the generated service file into `/etc/systemd/system/`, reloads
    the systemd daemon, and enables the service to start on boot.
    """
    print("\n=== Configuring Autostart ===")
    
    # Copy service file to systemd directory
    run_command("sudo cp bluespace-hardware-notifier.service /etc/systemd/system/", 
                "Copy systemd service file")
    
    # Enable and start the service
    run_command("sudo systemctl daemon-reload", "Reload systemd daemon")
    run_command("sudo systemctl enable bluespace-hardware-notifier.service", 
                "Enable hardware notifier service")
    
    print("✓ Autostart configured")

def create_monitoring_script():
    """Create a monitoring script for service, GPIO, display, and network.

    Writes `monitor_hardware.py`, a CLI utility that reports the status of the
    `bluespace-hardware-notifier.service`, performs a minimal GPIO operation,
    checks display availability via Pygame, and performs a network call to the
    configured server (`config.SERVER_URL`).
    """
    print("\n=== Creating Monitoring Script ===")
    
    monitoring_script = '''#!/usr/bin/env python3
"""
Hardware Notifier Monitoring Script
Monitors the status of the hardware notifier and provides diagnostics
"""

import os
import sys
import time
import json
import subprocess
import requests
from datetime import datetime

def check_service_status():
    """Check if the hardware notifier service is running"""
    try:
        result = subprocess.run(['systemctl', 'is-active', 'bluespace-hardware-notifier.service'], 
                              capture_output=True, text=True)
        return result.stdout.strip() == 'active'
    except:
        return False

def check_gpio_status():
    """Check GPIO status"""
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        
        # Test a simple GPIO operation
        test_pin = 17
        GPIO.setup(test_pin, GPIO.OUT)
        GPIO.output(test_pin, GPIO.LOW)
        GPIO.cleanup()
        return True
    except Exception as e:
        print(f"GPIO Error: {e}")
        return False

def check_display_status():
    """Check display status"""
    try:
        import pygame
        pygame.init()
        info = pygame.display.Info()
        pygame.quit()
        return info.current_w > 0 and info.current_h > 0
    except Exception as e:
        print(f"Display Error: {e}")
        return False

def check_network_connectivity():
    """Check network connectivity to the server"""
    try:
        from config import SERVER_URL
        response = requests.get(f"{SERVER_URL}/api/orders", timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Network Error: {e}")
        return False

def main():
    """Main monitoring function"""
    print("BlueSpace Restaurant Hardware Notifier - Status Monitor")
    print("=" * 60)
    
    # Check service status
    service_running = check_service_status()
    print(f"Service Status: {'✓ Running' if service_running else '✗ Stopped'}")
    
    # Check GPIO
    gpio_ok = check_gpio_status()
    print(f"GPIO Status: {'✓ OK' if gpio_ok else '✗ Error'}")
    
    # Check display
    display_ok = check_display_status()
    print(f"Display Status: {'✓ OK' if display_ok else '✗ Error'}")
    
    # Check network
    network_ok = check_network_connectivity()
    print(f"Network Status: {'✓ OK' if network_ok else '✗ Error'}")
    
    # Overall status
    overall_ok = service_running and gpio_ok and display_ok and network_ok
    print(f"Overall Status: {'✓ All Systems OK' if overall_ok else '✗ Issues Detected'}")
    
    # Show logs
    print("\\nRecent Logs:")
    try:
        with open('hardware_notifier.log', 'r') as f:
            lines = f.readlines()
            for line in lines[-10:]:  # Last 10 lines
                print(line.strip())
    except FileNotFoundError:
        print("No log file found")

if __name__ == "__main__":
    main()
'''
    
    with open('monitor_hardware.py', 'w') as f:
        f.write(monitoring_script)
    
    run_command("chmod +x monitor_hardware.py", "Make monitoring script executable")
    print("✓ Monitoring script created")

def main():
    """Run all setup steps in sequence and print next actions."""
    print("BlueSpace Restaurant Hardware Notifier - Quick Setup")
    print("=" * 50)
    
    # Run setup steps
    install_essential_packages()
    configure_gpio()
    create_startup_script()
    configure_autostart()
    create_monitoring_script()
    
    print("\n" + "=" * 50)
    print("Quick setup completed successfully!")
    print("\nNext steps:")
    print("1. Test GPIO: python3 test_gpio.py")
    print("2. Test hardware notifier: python3 hardware_notifier.py")
    print("3. Monitor status: python3 monitor_hardware.py")
    print("4. Start service: sudo systemctl start bluespace-hardware-notifier.service")
    print("5. Check service: sudo systemctl status bluespace-hardware-notifier.service")

if __name__ == "__main__":
    main() 