#!/bin/bash

# BlueSpace Hardware Notifier Service Installer
# This script installs the hardware notifier as a systemd service

echo "Installing BlueSpace Hardware Notifier Service..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="bluespace-hardware-notifier.service"

# Check if service file exists
if [ ! -f "$SCRIPT_DIR/$SERVICE_FILE" ]; then
    echo "Error: Service file not found at $SCRIPT_DIR/$SERVICE_FILE"
    exit 1
fi

# Copy service file to systemd directory
cp "$SCRIPT_DIR/$SERVICE_FILE" /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable the service (start at boot)
systemctl enable bluespace-hardware-notifier.service

# Start the service
systemctl start bluespace-hardware-notifier.service

# Check status
echo "Service status:"
systemctl status bluespace-hardware-notifier.service --no-pager

echo ""
echo "Installation complete!"
echo "The hardware notifier will now start automatically at boot."
echo ""
echo "Useful commands:"
echo "  Check status: sudo systemctl status bluespace-hardware-notifier"
echo "  Start service: sudo systemctl start bluespace-hardware-notifier"
echo "  Stop service: sudo systemctl stop bluespace-hardware-notifier"
echo "  View logs: sudo journalctl -u bluespace-hardware-notifier -f"
echo "  Disable auto-start: sudo systemctl disable bluespace-hardware-notifier"
