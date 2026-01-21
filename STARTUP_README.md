# BlueSpace Hardware Notifier Startup System

This directory contains scripts to automatically start the BlueSpace Hardware Notifier on boot.

## Quick Start (Recommended)

Use the unified installer which sets up a single systemd service and disables legacy ones to avoid conflicts:

```bash
sudo bash scripts/install-notifier-service.sh
sudo systemctl status bluespace-notifier.service | cat
```

Notes:
- If you have a virtualenv at `venv/`, it will be used; otherwise system Python is used.
- The service starts after network and the graphical session, and sets DISPLAY, XAUTHORITY, XDG_RUNTIME_DIR, SDL_VIDEODRIVER.
- Override SDL driver with `SDL_DRIVER=wayland` if needed.

## Files Overview

### Core Files
- `start_hardware_notifier.sh` - Main startup script with error handling and logging
- `install_startup.sh` - Installation script that sets up automatic startup
- `setup_crontab_startup.sh` - Sets up crontab-based startup

### Service Files
- `scripts/install-notifier-service.sh` - Unified installer creating `/etc/systemd/system/bluespace-notifier.service`

### Python Files
- `run_hardware_notifier.py` - Python runner script
- `hardware_notifier.py` - Main hardware notifier module
- `config.py` - Configuration file

## Startup Methods

### 1. Systemd Service (Recommended)
Managed by the installer:

```bash
sudo bash scripts/install-notifier-service.sh
# Management
sudo systemctl status bluespace-notifier.service
sudo systemctl stop bluespace-notifier.service
sudo systemctl restart bluespace-notifier.service
sudo journalctl -u bluespace-notifier.service -f
```

### 2. Crontab (Optional)
Prefer systemd. Use only if required by your environment.

### 3. rc.local (Not Recommended)
Use only for legacy systems without systemd.

## Monitoring and Troubleshooting

### Check if Hardware Notifier is Running
```bash
ps aux | grep run_hardware_notifier
ps aux | grep hardware_notifier
```

### View Logs
```bash
# Hardware notifier logs
tail -f hardware_notifier.log

# Systemd logs
sudo journalctl -u bluespace-notifier.service -f
```

### Check PID File
```bash
cat hardware_notifier.pid
```

### Manual Testing
```bash
# Test the startup script
./start_hardware_notifier.sh

# Test the Python script directly
python3 run_hardware_notifier.py
```

## Common Issues and Solutions

### Issue: 203/EXEC Error in Systemd
**Cause:** Path issues, missing dependencies, or permission problems
**Solution:** Use the startup script which handles these issues

### Issue: Hardware Notifier Not Starting
**Cause:** Missing dependencies or configuration issues
**Solution:** Check the startup log file for specific errors

### Issue: Permission Denied
**Cause:** Script not executable or wrong user
**Solution:** 
```bash
chmod +x start_hardware_notifier.sh
chmod +x run_hardware_notifier.py
```

### Issue: GPIO Access Denied
**Cause:** User not in gpio group
**Solution:**
```bash
sudo usermod -a -G gpio pi
sudo reboot
```

## Configuration

The hardware notifier uses `config.py` for configuration. Key settings:

- `SERVER_URL` - Your BlueSpace server URL
- `RESTAURANT_ID` - Your restaurant ID
- GPIO pin assignments for LEDs and buzzer
- Notification patterns and timing

## Environment Variables

The startup script sets these environment variables:

- `PYTHONPATH` - Points to the project directory
- `SIMULATION_MODE` - Set to "false" for real hardware
- `PYTHONUNBUFFERED` - Ensures immediate log output

## Security Notes

- The startup script runs as the `pi` user (not root)
- GPIO access requires the user to be in the `gpio` group
- All scripts include proper error handling and cleanup

## Support

If you encounter issues:

1. Check the log files for specific error messages
2. Test the startup script manually
3. Verify all dependencies are installed
4. Ensure proper permissions and group membership

For additional help, check the main project README or contact support. 