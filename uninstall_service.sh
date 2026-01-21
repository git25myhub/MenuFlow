#!/bin/bash

# BlueSpace Hardware Notifier Service Uninstaller

echo "Uninstalling BlueSpace Hardware Notifier Service..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

# Stop the service
systemctl stop bluespace-hardware-notifier.service

# Disable the service
systemctl disable bluespace-hardware-notifier.service

# Remove the service file
rm -f /etc/systemd/system/bluespace-hardware-notifier.service

# Reload systemd
systemctl daemon-reload

echo "Service uninstalled successfully!"
echo "The hardware notifier will no longer start automatically at boot."
