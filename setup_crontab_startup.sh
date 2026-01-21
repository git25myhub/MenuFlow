#!/bin/bash

# Setup script for crontab-based startup of hardware notifier
# This is often more reliable than systemd for simple applications

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STARTUP_SCRIPT="$SCRIPT_DIR/start_hardware_notifier.sh"

echo "Setting up crontab-based startup for BlueSpace Hardware Notifier..."

# Make the startup script executable
chmod +x "$STARTUP_SCRIPT"
echo "Made startup script executable: $STARTUP_SCRIPT"

# Create a temporary crontab entry
TEMP_CRON=$(mktemp)

# Get current crontab
crontab -l 2>/dev/null > "$TEMP_CRON" || echo "" > "$TEMP_CRON"

# Check if the entry already exists
if grep -q "start_hardware_notifier.sh" "$TEMP_CRON"; then
    echo "Crontab entry already exists. Removing old entry..."
    sed -i '/start_hardware_notifier.sh/d' "$TEMP_CRON"
fi

# Add new crontab entry to start on boot and restart every 5 minutes if not running
echo "# BlueSpace Hardware Notifier - Start on boot and restart if needed" >> "$TEMP_CRON"
echo "@reboot $STARTUP_SCRIPT" >> "$TEMP_CRON"
echo "*/5 * * * * $STARTUP_SCRIPT" >> "$TEMP_CRON"

# Install the new crontab
crontab "$TEMP_CRON"

# Clean up
rm "$TEMP_CRON"

echo "Crontab setup complete!"
echo ""
echo "Current crontab entries:"
crontab -l | grep -A 2 -B 2 "start_hardware_notifier"
echo ""
echo "The hardware notifier will now:"
echo "1. Start automatically on boot"
echo "2. Restart every 5 minutes if it's not running"
echo ""
echo "To test the startup script manually, run:"
echo "  $STARTUP_SCRIPT"
echo ""
echo "To view logs:"
echo "  tail -f $SCRIPT_DIR/hardware_notifier_startup.log"
echo ""
echo "To remove crontab entries:"
echo "  crontab -e"
echo "  (then delete the lines with start_hardware_notifier.sh)" 