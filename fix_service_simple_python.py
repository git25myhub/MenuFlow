#!/usr/bin/env python3
"""
Simple Python Service Fix
Uses existing run_hardware_notifier.py directly
"""

import os
import subprocess

def fix_systemd_service():
    """Fix the systemd service configuration"""
    print("Fixing systemd service configuration (Simple Python approach)...")
    
    # Service file content using existing script
    service_content = """[Unit]
Description=BlueSpace Restaurant Hardware Notifier
After=network.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi/BlueSpace Restaurants
ExecStart=/home/pi/BlueSpace Restaurants/venv/bin/python3 /home/pi/BlueSpace Restaurants/run_hardware_notifier.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment=SIMULATION_MODE=false

[Install]
WantedBy=multi-user.target
"""
    
    try:
        # Write the service file
        with open('bluespace-hardware-notifier.service', 'w') as f:
            f.write(service_content)
        
        print("✓ Service file updated with simple Python approach")
        
        # Copy to systemd directory
        subprocess.run(['sudo', 'cp', 'bluespace-hardware-notifier.service', '/etc/systemd/system/'], check=True)
        print("✓ Service file copied to systemd directory")
        
        # Reload systemd
        subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
        print("✓ Systemd daemon reloaded")
        
        # Enable service
        subprocess.run(['sudo', 'systemctl', 'enable', 'bluespace-hardware-notifier.service'], check=True)
        print("✓ Service enabled")
        
        print("\nService fixed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Error: {e}")
        return False
    except Exception as e:
        print(f"✗ Exception: {e}")
        return False

if __name__ == "__main__":
    fix_systemd_service() 