#!/bin/bash

# BlueSpace Hardware Notifier Startup Installation Script
# This script sets up automatic startup for the hardware notifier

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

echo "=== BlueSpace Hardware Notifier Startup Installation ==="
echo "Project directory: $PROJECT_DIR"
echo ""

# Function to check if running as root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        echo "ERROR: This script should not be run as root"
        echo "Please run as the pi user: sudo -u pi ./install_startup.sh"
        exit 1
    fi
}

# Function to make scripts executable
make_executable() {
    echo "Making scripts executable..."
    chmod +x "$PROJECT_DIR/start_hardware_notifier.sh"
    chmod +x "$PROJECT_DIR/setup_crontab_startup.sh"
    chmod +x "$PROJECT_DIR/run_hardware_notifier.py"
    echo "✓ Scripts made executable"
}

# Function to test the startup script
test_startup_script() {
    echo ""
    echo "Testing startup script..."
    if [ -f "$PROJECT_DIR/start_hardware_notifier.sh" ]; then
        echo "✓ Startup script exists"
        
        # Test if it can be executed
        if bash -n "$PROJECT_DIR/start_hardware_notifier.sh"; then
            echo "✓ Startup script syntax is valid"
        else
            echo "✗ Startup script has syntax errors"
            return 1
        fi
    else
        echo "✗ Startup script not found"
        return 1
    fi
}

# Function to setup systemd service
setup_systemd() {
    echo ""
    echo "Setting up systemd service..."
    
    SERVICE_FILE="/etc/systemd/system/bluespace-hardware-notifier.service"
    SOURCE_FILE="$PROJECT_DIR/bluespace-hardware-notifier-simple.service"
    
    if [ ! -f "$SOURCE_FILE" ]; then
        echo "✗ Service file not found: $SOURCE_FILE"
        return 1
    fi
    
    # Copy service file (requires sudo)
    echo "Copying service file to systemd directory..."
    sudo cp "$SOURCE_FILE" "$SERVICE_FILE"
    
    # Reload systemd
    echo "Reloading systemd..."
    sudo systemctl daemon-reload
    
    # Enable service
    echo "Enabling service..."
    sudo systemctl enable bluespace-hardware-notifier.service
    
    echo "✓ Systemd service setup complete"
    echo "  Service file: $SERVICE_FILE"
    echo "  To start: sudo systemctl start bluespace-hardware-notifier"
    echo "  To stop: sudo systemctl stop bluespace-hardware-notifier"
    echo "  To check status: sudo systemctl status bluespace-hardware-notifier"
}

# Function to setup crontab
setup_crontab() {
    echo ""
    echo "Setting up crontab startup..."
    
    if [ -f "$PROJECT_DIR/setup_crontab_startup.sh" ]; then
        bash "$PROJECT_DIR/setup_crontab_startup.sh"
        echo "✓ Crontab setup complete"
    else
        echo "✗ Crontab setup script not found"
        return 1
    fi
}

# Function to create a simple rc.local entry
setup_rclocal() {
    echo ""
    echo "Setting up rc.local startup..."
    
    RCLOCAL="/etc/rc.local"
    STARTUP_CMD="cd $PROJECT_DIR && ./start_hardware_notifier.sh &"
    
    # Check if rc.local exists
    if [ ! -f "$RCLOCAL" ]; then
        echo "Creating rc.local file..."
        sudo tee "$RCLOCAL" > /dev/null <<EOF
#!/bin/bash
# This file is executed at the end of each multiuser runlevel.
# Make sure that the script will "exit 0" on success or any other
# value on error.

$STARTUP_CMD

exit 0
EOF
    else
        # Check if entry already exists
        if grep -q "start_hardware_notifier.sh" "$RCLOCAL"; then
            echo "✓ rc.local entry already exists"
        else
            echo "Adding startup command to rc.local..."
            # Insert before the last line (exit 0)
            sudo sed -i "s/^exit 0$/$STARTUP_CMD\n\nexit 0/" "$RCLOCAL"
        fi
    fi
    
    # Make rc.local executable
    sudo chmod +x "$RCLOCAL"
    
    echo "✓ rc.local setup complete"
}

# Main installation
main() {
    check_root
    make_executable
    test_startup_script
    
    echo ""
    echo "Choose startup method:"
    echo "1. Systemd service (recommended for modern systems)"
    echo "2. Crontab (simple and reliable)"
    echo "3. rc.local (traditional method)"
    echo "4. All methods (for maximum reliability)"
    echo ""
    read -p "Enter your choice (1-4): " choice
    
    case $choice in
        1)
            setup_systemd
            ;;
        2)
            setup_crontab
            ;;
        3)
            setup_rclocal
            ;;
        4)
            setup_systemd
            setup_crontab
            setup_rclocal
            ;;
        *)
            echo "Invalid choice. Exiting."
            exit 1
            ;;
    esac
    
    echo ""
    echo "=== Installation Complete ==="
    echo ""
    echo "Next steps:"
    echo "1. Test the startup script manually:"
    echo "   $PROJECT_DIR/start_hardware_notifier.sh"
    echo ""
    echo "2. Monitor the logs:"
    echo "   tail -f $PROJECT_DIR/hardware_notifier_startup.log"
    echo ""
    echo "3. Reboot to test automatic startup:"
    echo "   sudo reboot"
    echo ""
    echo "4. Check if it's running:"
    echo "   ps aux | grep run_hardware_notifier"
    echo ""
    echo "For troubleshooting, check:"
    echo "  - $PROJECT_DIR/hardware_notifier_startup.log"
    echo "  - journalctl -u bluespace-hardware-notifier (if using systemd)"
    echo "  - crontab -l (if using crontab)"
}

# Run main function
main "$@" 