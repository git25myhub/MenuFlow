# Display System Troubleshooting Guide

## Why the Display Isn't Working

The Raspberry Pi display system has different requirements than the GPIO pins (LEDs/buzzer):

### 1. **Display Dependencies**
- **Pygame**: Requires proper X11 environment
- **PIL**: Image processing library
- **X11 Server**: Must be running and accessible

### 2. **Environment Variables**
- `DISPLAY=:0` - X11 display number
- `XAUTHORITY` - X11 authentication file
- `XDG_RUNTIME_DIR` - Runtime directory for user

### 3. **User Context**
- Must run as `pi` user (not root)
- Must have access to X11 socket
- Desktop must be logged in

## Quick Fixes

### **Fix 1: Check Display Environment**
```bash
# Test display system
python3 test_display.py

# Check if X11 is running
ps aux | grep X

# Check display socket
ls -la /tmp/.X11-unix/
```

### **Fix 2: Fix X11 Permissions**
```bash
# Allow local connections
xhost +local:

# Fix socket permissions
sudo chmod 1777 /tmp/.X11-unix
sudo chown root:root /tmp/.X11-unix
```

### **Fix 3: Restart Desktop**
```bash
# Restart lightdm (desktop manager)
sudo systemctl restart lightdm

# Wait for desktop to load, then test
python3 test_display.py
```

### **Fix 4: Check User Login**
```bash
# Make sure you're logged in to desktop (not just SSH)
# The display won't work if you're only connected via SSH

# Check current user
whoami

# Check if pi user is logged in
who
```

## Detailed Troubleshooting

### **Step 1: Test Display Manually**
```bash
# Run the test script
python3 test_display.py

# Look for specific error messages
```

### **Step 2: Check System Status**
```bash
# Check if desktop is running
systemctl status lightdm

# Check X11 process
ps aux | grep X

# Check display environment
echo $DISPLAY
echo $XAUTHORITY
```

### **Step 3: Fix Common Issues**

#### **Issue: "No display detected"**
```bash
# Set display environment
export DISPLAY=:0
export XAUTHORITY=/home/pi/.Xauthority

# Test again
python3 test_display.py
```

#### **Issue: "Permission denied"**
```bash
# Fix X11 permissions
sudo chmod 1777 /tmp/.X11-unix
sudo chown root:root /tmp/.X11-unix

# Allow local connections
xhost +local:
```

#### **Issue: "Cannot open display"**
```bash
# Check if X11 is running
ps aux | grep X

# If not running, restart desktop
sudo systemctl restart lightdm

# Wait for desktop to load, then test
```

### **Step 4: Test Hardware Notifier Display**
```bash
# Test with simulation mode first
python3 hardware_notifier.py --test

# Test with real hardware
python3 hardware_notifier.py --simulate false
```

## Service Configuration

### **Update Service File**
The service file now includes proper display environment variables:

```ini
[Service]
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/pi/.Xauthority
Environment=XDG_RUNTIME_DIR=/run/user/1000
After=graphical.target
Requires=graphical.target
```

### **Reinstall Service**
```bash
# Stop current service
sudo systemctl stop bluespace-hardware-notifier

# Reinstall with new configuration
sudo ./install_service.sh

# Check status
sudo systemctl status bluespace-hardware-notifier
```

## Alternative Display Modes

### **Framebuffer Mode**
If X11 doesn't work, try framebuffer mode:

```bash
# Set framebuffer environment
export SDL_VIDEODRIVER=fbcon
export SDL_FBDEV=/dev/fb0

# Test display
python3 test_display.py
```

### **TTY Mode**
For headless operation without display:

```bash
# Set simulation mode
export SIMULATION_MODE=true

# Run hardware notifier (LEDs/buzzer only)
python3 hardware_notifier.py --simulate true
```

## Monitoring and Debugging

### **Check Service Logs**
```bash
# View real-time logs
sudo journalctl -u bluespace-hardware-notifier -f

# View recent logs
sudo journalctl -u bluespace-hardware-notifier -n 50
```

### **Check Display Thread**
```bash
# Check if display thread is running
ps aux | grep "HardwareNotifier-Display"

# Check hardware notifier status
python3 -c "
from hardware_notifier import get_hardware_notifier
notifier = get_hardware_notifier(simulation_mode=False)
print(f'Display thread alive: {notifier.display_thread and notifier.display_thread.is_alive()}')
print(f'Display surface: {notifier.display_surface is not None}')
"
```

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "No display detected" | X11 not running | Restart desktop, check permissions |
| "Cannot open display" | Permission denied | Fix X11 permissions, run as pi user |
| "pygame.error: No available video device" | No display access | Check DISPLAY variable, login to desktop |
| "Permission denied" | X11 socket permissions | Fix /tmp/.X11-unix permissions |

## Success Indicators

When the display is working correctly, you should see:

1. **Service Status**: `Active (running)` with no errors
2. **Display Thread**: Running and alive
3. **Log Messages**: "Display system initialized successfully"
4. **Visual Output**: Kitchen orders displayed on screen
5. **Real-time Updates**: Orders appearing/disappearing as they change

## Still Not Working?

If none of the above fixes work:

1. **Check Hardware**: Ensure HDMI cable is connected and monitor is on
2. **Check OS**: Make sure you're running Raspberry Pi OS with desktop
3. **Check Dependencies**: Install pygame and PIL: `sudo apt install python3-pygame python3-pil`
4. **Check User**: Ensure running as `pi` user, not root
5. **Check Desktop**: Make sure desktop is fully loaded and logged in

## Contact Support

If you're still having issues, provide:
- Output from `python3 test_display.py`
- Service logs: `sudo journalctl -u bluespace-hardware-notifier -n 100`
- System info: `uname -a`, `cat /etc/os-release`
- Display environment: `env | grep -E "(DISPLAY|XAUTHORITY|XDG)"`
