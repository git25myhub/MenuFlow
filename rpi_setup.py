#!/usr/bin/env python3
"""
Raspberry Pi Setup Script for BlueSpace Restaurant Hardware Notifier

This script sets up the Raspberry Pi 4B for the restaurant hardware notification system.
It installs dependencies, configures GPIO pins, and sets up the display system.
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path

def run_command(command, description=""):
    """Run a shell command and handle errors"""
    print(f"Running: {description or command}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description or command} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"✗ Error running '{command}': {e}")
        print(f"Error output: {e.stderr}")
        return None

def check_raspberry_pi():
    """Check if running on Raspberry Pi"""
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpu_info = f.read()
            if 'Raspberry Pi' in cpu_info:
                print("✓ Running on Raspberry Pi")
                return True
            else:
                print("✗ Not running on Raspberry Pi")
                return False
    except FileNotFoundError:
        print("✗ Cannot determine if running on Raspberry Pi")
        return False

def update_system():
    """Update the system packages"""
    print("\n=== Updating System Packages ===")
    run_command("sudo apt update", "Update package list")
    # Skip system upgrade as it takes too long and may not be necessary
    print("⚠ Skipping system upgrade (can be done manually later if needed)")
    # run_command("sudo apt upgrade -y", "Upgrade system packages")

def install_python_dependencies():
    """Install Python dependencies"""
    print("\n=== Installing Python Dependencies ===")
    
    # Install system dependencies
    system_packages = [
        "python3-pip",
        "python3-venv",
        "python3-dev",
        "libatlas-base-dev",  # For numpy
        "libopenjp2-7-dev",   # For PIL
        "libtiff5-dev",       # For PIL
        "libjpeg-dev",        # For PIL
        "libfreetype6-dev",   # For PIL
        "liblcms2-dev",       # For PIL
        "libwebp-dev",        # For PIL
        "libharfbuzz-dev",    # For PIL
        "libfribidi-dev",     # For PIL
        "libxcb1-dev",        # For pygame
        "libxrandr-dev",      # For pygame
        "libasound2-dev",     # For pygame
        "libpulse-dev",       # For pygame
        "libvorbis-dev",      # For pygame
        "libflac-dev",        # For pygame
        "libmodplug-dev",     # For pygame
        "libsmpeg-dev",       # For pygame
        "libsdl2-dev",        # For pygame
        "libsdl2-image-dev",  # For pygame
        "libsdl2-mixer-dev",  # For pygame
        "libsdl2-ttf-dev",    # For pygame
        "libportmidi-dev",    # For pygame
        "libswscale-dev",     # For pygame
        "libavformat-dev",    # For pygame
        "libavcodec-dev",     # For pygame
        "libavdevice-dev",    # For pygame
        "libavutil-dev",      # For pygame
        "libpostproc-dev",    # For pygame
        "libswresample-dev",  # For pygame
        "libavfilter-dev",    # For pygame
    ]
    
    for package in system_packages:
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
    """Configure GPIO pins for the hardware notifier"""
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

def configure_display():
    """Configure display settings"""
    print("\n=== Configuring Display ===")
    
    # Enable SPI and I2C if needed
    run_command("sudo raspi-config nonint do_spi 0", "Enable SPI")
    run_command("sudo raspi-config nonint do_i2c 0", "Enable I2C")
    
    # Configure display settings
    display_config = {
        "fullscreen": True,
        "resolution": "auto",
        "refresh_rate": 60,
        "vsync": True,
    }
    
    with open('display_config.json', 'w') as f:
        json.dump(display_config, f, indent=2)
    
    print("✓ Display configuration saved")

def create_startup_script():
    """Create startup script for the hardware notifier"""
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
    """Configure autostart for the hardware notifier"""
    print("\n=== Configuring Autostart ===")
    
    # Copy service file to systemd directory
    run_command("sudo cp bluespace-hardware-notifier.service /etc/systemd/system/", 
                "Copy systemd service file")
    
    # Enable and start the service
    run_command("sudo systemctl daemon-reload", "Reload systemd daemon")
    run_command("sudo systemctl enable bluespace-hardware-notifier.service", 
                "Enable hardware notifier service")
    run_command("sudo systemctl start bluespace-hardware-notifier.service", 
                "Start hardware notifier service")
    
    print("✓ Autostart configured")

def create_monitoring_script():
    """Create a monitoring script for the hardware notifier"""
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

def create_documentation():
    """Create documentation for the hardware setup"""
    print("\n=== Creating Documentation ===")
    
    documentation = '''# BlueSpace Restaurant Hardware Notifier - Raspberry Pi Setup

## Overview
This document describes the setup and operation of the BlueSpace Restaurant Hardware Notifier on Raspberry Pi 4B.

## Hardware Requirements
- Raspberry Pi 4B (2GB RAM minimum, 4GB recommended)
- MicroSD card (32GB minimum)
- Power supply (5V/3A minimum)
- HDMI monitor or display
- LED indicators (optional)
- Buzzer (optional)
- Breadboard and jumper wires (for LED/buzzer connection)

## GPIO Pin Configuration
- GPIO17: Dine-in LED indicator
- GPIO27: Delivery LED indicator  
- GPIO22: Buzzer
- GPIO18: Status LED (optional)

## Installation
1. Run the setup script: `python3 rpi_setup.py`
2. Connect hardware components to GPIO pins
3. Test the setup: `python3 test_gpio.py`
4. Start the hardware notifier: `./start_hardware_notifier.sh`

## Operation
The hardware notifier will:
- Monitor for new orders from the restaurant website
- Display orders on the screen in slide mode
- Trigger LED indicators for different notification types
- Sound buzzer alerts for important events
- Auto-restart on failure

## Monitoring
Use the monitoring script to check system status:
```bash
python3 monitor_hardware.py
```

## Troubleshooting
1. Check service status: `sudo systemctl status bluespace-hardware-notifier.service`
2. View logs: `tail -f hardware_notifier.log`
3. Test GPIO: `python3 test_gpio.py`
4. Check network connectivity to the server

## Configuration Files
- `config.py`: Main configuration
- `gpio_config.json`: GPIO pin assignments
- `display_config.json`: Display settings

## Support
For issues or questions, check the logs and monitoring output.
'''
    
    with open('HARDWARE_SETUP.md', 'w') as f:
        f.write(documentation)
    
    print("✓ Documentation created")

def main():
    """Main setup function"""
    print("BlueSpace Restaurant Hardware Notifier Setup")
    print("=" * 50)
    
    # Check if running on Raspberry Pi
    if not check_raspberry_pi():
        print("Warning: This script is designed for Raspberry Pi. Continue anyway? (y/N)")
        response = input().lower()
        if response != 'y':
            print("Setup cancelled.")
            return
    
    # Run setup steps
    update_system()
    install_python_dependencies()
    configure_gpio()
    configure_display()
    create_startup_script()
    configure_autostart()
    create_monitoring_script()
    create_documentation()
    
    print("\n" + "=" * 50)
    print("Setup completed successfully!")
    print("\nNext steps:")
    print("1. Connect hardware components to GPIO pins")
    print("2. Test GPIO: python3 test_gpio.py")
    print("3. Test hardware notifier: python3 hardware_notifier.py")
    print("4. Monitor status: python3 monitor_hardware.py")
    print("5. Check service: sudo systemctl status bluespace-hardware-notifier.service")
    print("\nDocumentation: HARDWARE_SETUP.md")

if __name__ == "__main__":
    main() 