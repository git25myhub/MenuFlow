# Raspberry Pi Hardware Notifier Setup Guide

This guide will help you set up and test the BlueSpace Restaurant Hardware Notifier on a Raspberry Pi with real hardware components.

## Prerequisites

### Hardware Requirements
- Raspberry Pi 4B (recommended) or Raspberry Pi 3B+
- MicroSD card (16GB or larger)
- Power supply for Raspberry Pi
- HDMI display or monitor
- LED lights (optional, for visual notifications)
- Buzzer/speaker (optional, for audio notifications)
- Breadboard and jumper wires (for LED/buzzer connections)

### Software Requirements
- Raspberry Pi OS (Bullseye or newer)
- Python 3.7+
- Internet connection

## Installation Steps

### 1. Install Required Packages

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python dependencies
sudo apt install python3-pip python3-venv python3-dev -y

# Install system dependencies for GPIO and display
sudo apt install python3-rpi.gpio python3-pygame -y

# Install additional dependencies
sudo apt install git curl -y
```

### 2. Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv hardware_env
source hardware_env/bin/activate

# Install required Python packages
pip install flask flask-socketio requests pillow gevent
```

### 3. Hardware Connections (Optional)

If you want to test LED and buzzer functionality:

#### LED Connections:
- Connect LED to GPIO17 (DINE_IN_LED_PIN)
- Connect LED to GPIO27 (DELIVERY_LED_PIN)
- Use appropriate resistors (220-330 ohms)

#### Buzzer Connection:
- Connect buzzer to GPIO22 (BUZZER_PIN)

**Note:** If you don't have physical LEDs/buzzer, the system will still work and log the notifications.

### 4. Configure the System

1. **Edit config.py** to set your restaurant ID:
   ```python
   RESTAURANT_ID = 2  # Change this to your restaurant's ID
   ```

2. **Verify server URL** in config.py:
   ```python
   SERVER_URL = "https://bluespace-restaurants.onrender.com"
   ```

## Testing the Hardware Notifier

### 1. Run the Comprehensive Test

```bash
# Activate virtual environment
source hardware_env/bin/activate

# Run the test script
python3 test_raspberry_pi.py
```

This will test:
- ✅ GPIO availability
- ✅ Display functionality
- ✅ Network connectivity
- ✅ LED patterns
- ✅ Buzzer patterns
- ✅ Order fetching
- ✅ Web interface

### 2. Start the Hardware Notifier

```bash
# Start the web interface
python3 hardware_web_interface.py
```

The web interface will be available at: `http://your-raspberry-pi-ip:5001`

### 3. Test Notifications

You can test notifications through the web interface or by sending API requests:

```bash
# Test a new order notification
curl -X POST http://localhost:5001/api/test-notification \
  -H "Content-Type: application/json" \
  -d '{"type": "NEW_ORDER", "priority": 1}'
```

## Expected Behavior

### Display
- The display should show "Restaurant #2 - Kitchen Orders" (or your restaurant ID)
- Orders will be displayed in a grid layout
- New orders will appear automatically
- Delivered orders will be removed automatically

### LED Notifications
- **New Order**: GPIO17 blinks 3 times
- **Order Ready**: GPIO27 pulses 2 times
- **Order Delivered**: GPIO27 solid light
- **Payment Received**: GPIO17 blinks 4 times

### Buzzer Notifications
- **New Order**: 440Hz beep (3 times)
- **Order Ready**: 880Hz beep (2 times)
- **Order Delivered**: 660Hz beep (1 time)
- **Payment Received**: 550Hz beep (4 times)

## Troubleshooting

### Common Issues

1. **GPIO Permission Error**
   ```bash
   # Add user to gpio group
   sudo usermod -a -G gpio $USER
   # Reboot or log out/in
   ```

2. **Display Not Working**
   ```bash
   # Check if display is detected
   python3 -c "import pygame; pygame.init(); print(pygame.display.Info())"
   ```

3. **Network Connectivity Issues**
   ```bash
   # Test server connectivity
   curl https://bluespace-restaurants.onrender.com/api/orders?restaurant_id=2
   ```

4. **Port Already in Use**
   ```bash
   # Check what's using port 5001
   sudo netstat -tulpn | grep 5001
   # Kill the process if needed
   sudo kill -9 <PID>
   ```

### Logs

Check the logs for detailed information:
```bash
# View hardware notifier logs
tail -f hardware_notifier.log

# View system logs
sudo journalctl -f
```

## Production Deployment

### 1. Create a Systemd Service

Create `/etc/systemd/system/hardware-notifier.service`:

```ini
[Unit]
Description=BlueSpace Restaurant Hardware Notifier
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/hardware-notifier
Environment=PATH=/home/pi/hardware-notifier/hardware_env/bin
ExecStart=/home/pi/hardware-notifier/hardware_env/bin/python hardware_web_interface.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Enable and Start the Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable hardware-notifier
sudo systemctl start hardware-notifier
sudo systemctl status hardware-notifier
```

### 3. Auto-start on Boot

Add to `/etc/rc.local` (before `exit 0`):
```bash
# Start hardware notifier
cd /home/pi/hardware-notifier && source hardware_env/bin/activate && python hardware_web_interface.py &
```

## Security Considerations

1. **Firewall**: Configure firewall to only allow necessary ports
2. **SSH**: Use SSH keys instead of passwords
3. **Updates**: Keep system updated regularly
4. **Network**: Use secure network connections

## Monitoring

### Health Check Script

Create a simple health check script:

```bash
#!/bin/bash
# health_check.sh

if ! curl -s http://localhost:5001/api/status > /dev/null; then
    echo "Hardware notifier is down, restarting..."
    sudo systemctl restart hardware-notifier
fi
```

Add to crontab to run every 5 minutes:
```bash
*/5 * * * * /home/pi/health_check.sh
```

## Support

If you encounter issues:

1. Check the logs: `tail -f hardware_notifier.log`
2. Run the test script: `python3 test_raspberry_pi.py`
3. Verify network connectivity
4. Check hardware connections
5. Ensure all dependencies are installed

The hardware notifier is now ready to run on your Raspberry Pi with real hardware components! 