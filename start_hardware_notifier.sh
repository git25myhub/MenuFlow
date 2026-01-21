#!/bin/bash

# BlueSpace Hardware Notifier Startup Script
# This script ensures proper display environment before starting the notifier

echo "Starting BlueSpace Hardware Notifier..."

# Set display environment variables
export DISPLAY=:0
export XAUTHORITY=/home/pi/.Xauthority
export XDG_RUNTIME_DIR=/run/user/1000

# Verify environment
echo "Display environment:"
echo "  DISPLAY: $DISPLAY"
echo "  XAUTHORITY: $XAUTHORITY"
echo "  XDG_RUNTIME_DIR: $XDG_RUNTIME_DIR"

# Check if X11 is accessible
if ! xset q >/dev/null 2>&1; then
    echo "ERROR: Cannot access X11 display. Make sure you're logged in to the desktop."
    echo "Try logging out and back in, or restart the desktop: sudo systemctl restart lightdm"
    exit 1
fi

echo "X11 display accessible ✓"

# Check if we're in the right directory
if [ ! -f "hardware_notifier.py" ]; then
    echo "ERROR: hardware_notifier.py not found in current directory"
    echo "Current directory: $(pwd)"
    exit 1
fi

echo "Hardware notifier found ✓"

# Start the hardware notifier
echo "Starting hardware notifier..."

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Start the hardware notifier with the virtual environment
echo "Starting hardware notifier with virtual environment..."
python3 hardware_notifier.py 