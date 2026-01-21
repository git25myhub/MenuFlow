# BlueSpace Restaurant Hardware Notifier

An automated setup and operational guide for deploying the BlueSpace Restaurant Hardware Notifier on a Raspberry Pi. This project provisions system and Python dependencies, configures GPIO, creates startup and monitoring utilities, and installs a systemd service for reliable autostart.

## Overview

- **Primary script**: `quick_setup.py`
- **What it does**:
  - Installs essential system packages and Python libraries
  - Writes a `gpio_config.json` file and a `test_gpio.py` utility
  - Creates a startup script `start_hardware_notifier.sh`
  - Generates a `bluespace-hardware-notifier.service` systemd unit
  - Provides a monitoring tool `monitor_hardware.py`

> Note: The tooling targets Raspberry Pi OS/Debian-based systems using `apt`, `systemd`, and Raspberry Pi GPIO via `RPi.GPIO`. Running on Windows or macOS is not supported for the hardware portions.

## Prerequisites

- Raspberry Pi (with 40-pin header recommended)
- Raspberry Pi OS (Bookworm/Bullseye) or Debian-based distro with `systemd`
- Internet connectivity
- Python 3.x and `pip3`
- Hardware connections to the following GPIOs (BCM numbering):
  - `DINE_IN_LED_PIN` (default 17)
  - `DELIVERY_LED_PIN` (default 27)
  - `BUZZER_PIN` (default 22)
  - `STATUS_LED_PIN` (default 18, optional)

## Quick Start

Run the setup script on your Raspberry Pi:

```bash
python3 quick_setup.py
```

When finished, you will see next steps printed, including how to test GPIO and manage the service.

## What the Setup Installs

`quick_setup.py` performs the following:

1. Installs system packages (development headers, SDL2 stack, audio libs, etc.) via `apt`.
2. Installs Python packages via `pip3`, including `RPi.GPIO`, `pygame`, `Flask`, `SQLAlchemy`, `requests`, `qrcode`, and more.
3. Writes `gpio_config.json` and a `test_gpio.py` script that toggles configured pins for validation.
4. Creates `start_hardware_notifier.sh` which:
   - cd's into `/home/pi/BlueSpace-Restaurants`
   - Activates `venv` if present
   - Exports environment variables (`SIMULATION_MODE`, `FLASK_ENV`, `FLASK_APP`)
   - Runs `hardware_notifier.py` and restarts it on exit
5. Creates a `bluespace-hardware-notifier.service` systemd unit to enable autostart.
6. Provides `monitor_hardware.py` to inspect service, GPIO, display, and network health.

## Generated Files

- `gpio_config.json`: Stores BCM pin numbers used by the notifier
- `test_gpio.py`: Simple GPIO exerciser based on `gpio_config.json`
- `start_hardware_notifier.sh`: Startup wrapper for the notifier process
- `bluespace-hardware-notifier.service`: systemd unit file
- `monitor_hardware.py`: Diagnostic and health monitoring tool

## GPIO Configuration

Default BCM pins can be changed by editing `gpio_config.json` after setup:

```json
{
  "DINE_IN_LED_PIN": 17,
  "DELIVERY_LED_PIN": 27,
  "BUZZER_PIN": 22,
  "STATUS_LED_PIN": 18
}
```

Test the configuration:

```bash
python3 test_gpio.py
```

## Service Management

The setup creates a systemd unit and provides commands to enable and manage it.

Enable autostart and start the service:

```bash
sudo cp bluespace-hardware-notifier.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable bluespace-hardware-notifier.service
sudo systemctl start bluespace-hardware-notifier.service
```

Check status and logs:

```bash
sudo systemctl status bluespace-hardware-notifier.service
journalctl -u bluespace-hardware-notifier.service -n 100 -f
```

Stop or disable:

```bash
sudo systemctl stop bluespace-hardware-notifier.service
sudo systemctl disable bluespace-hardware-notifier.service
```

## Monitoring and Diagnostics

Use the monitoring tool to check health indicators:

```bash
python3 monitor_hardware.py
```

It reports:

- Service running state
- GPIO basic operation
- Display availability via `pygame`
- Network connectivity to the configured server
- Tail of `hardware_notifier.log` if present

## Environment Variables

Set by `start_hardware_notifier.sh`:

- `SIMULATION_MODE` (default `false`): Run without real hardware if your notifier supports it
- `FLASK_ENV` (default `production`)
- `FLASK_APP` (default `app.py`)

You can extend the script or export additional variables as needed for your app.

## Network Configuration

`monitor_hardware.py` attempts to call `GET {SERVER_URL}/api/orders`. Ensure your application provides `config.py` with a value like:

```python
# config.py
SERVER_URL = "https://your-server.example.com"
```

Update `SERVER_URL` to match your backend endpoint.

## Logs

- Application logs: `hardware_notifier.log` (if your notifier writes to it)
- Service logs: `journalctl -u bluespace-hardware-notifier.service`

## Troubleshooting

- GPIO permission errors: Ensure you are running on Raspberry Pi OS and executing with appropriate permissions. Use `sudo` where necessary.
- `RPi.GPIO` import fails: Verify you are on a Raspberry Pi. This package is hardware-specific.
- Display errors with `pygame`: Make sure a display is attached or a virtual framebuffer is configured. SSH sessions without X may fail for display queries.
- Service does not start: Check `sudo systemctl status bluespace-hardware-notifier.service` and review logs.
- Network check fails in monitor: Verify `config.py` exists and `SERVER_URL` is reachable.

## Frequently Asked Questions

- Can I run this on Windows or macOS?
  - The hardware features are designed for Raspberry Pi/Linux. You can read files on other OSes, but GPIO and service management will not work.

- Where should the repo live on the Pi?
  - The startup script assumes `/home/pi/BlueSpace-Restaurants`. Adjust paths if you place it elsewhere.

- Do I need a virtual environment?
  - Optional. If `venv` exists in the project directory, it is activated by the startup script.

## Security Notes

- The startup script restarts the notifier after exit. Ensure your notifier handles credentials securely and avoid logging secrets.
- Keep your system updated and restrict network exposure of any admin endpoints.

## License

Proprietary or internal use unless otherwise specified by your organization. Update this section to reflect your chosen license.

# BlueSpace Restaurants 🍽️

A comprehensive restaurant management system built with Flask, featuring real-time order management, payment processing, and automated status transitions.

## 🌟 Features

### 🏪 Restaurant Management
- **Multi-restaurant support** with individual dashboards
- **Menu management** with categories and stock tracking
- **QR code generation** for easy menu access
- **Real-time order updates** via WebSocket and Server-Sent Events

### 📱 Order Management
- **Real-time order tracking** with live status updates
- **Automated status transitions** (new → pending → paid → preparing → ready → delivered)
- **Manual payment confirmation** workflow
- **Order cancellation** with automatic stock restoration
- **Special instructions** and delivery address support

### 💳 Payment Processing
- **Multiple payment methods**: Manual, M-Pesa, Pesapal
- **Payment status tracking** and confirmation
- **Manual payment review** system
- **Payment callback handling**

### 📊 Analytics & Reporting
- **Real-time dashboard** with order statistics
- **Revenue tracking** and daily summaries
- **Order analytics** and performance metrics
- **Export functionality** (PDF, CSV)

### 🔧 Technical Features
- **Optimized order status flow** with duplicate prevention
- **Real-time notifications** via WebSocket
- **Responsive design** for mobile and desktop
- **CSRF protection** and security measures
- **Database connection pooling** and optimization

## 🚀 Recent Optimizations

### Order Status Flow Improvements
- **Enhanced duplicate detection** preventing repeated status updates
- **Improved polling mechanism** with intelligent deduplication
- **Smooth status transitions** without UI fallbacks
- **Better memory management** for tracking systems
- **Optimized auto-transition timers** with proper cleanup

### Performance Enhancements
- **Reduced database queries** through better caching
- **Efficient WebSocket connections** with room-based updates
- **Smart order tracking** with status-based deduplication
- **Improved error handling** and logging throughout

### Hardware Notifier Optimizations
- **Professional notification system** with queuing and rate limiting
- **Multi-pattern support** (blink, pulse, solid) with configurable parameters
- **Priority-based processing** (5-level priority system)
- **Thread-safe operations** with proper synchronization
- **Automatic error recovery** and fallback to simulation mode
- **Comprehensive configuration** system with environment-specific settings
- **Performance monitoring** with real-time status tracking
- **Graceful shutdown** with proper resource cleanup

## 🛠️ Technology Stack

- **Backend**: Flask, SQLAlchemy, Flask-SocketIO
- **Database**: PostgreSQL (with connection pooling)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Payment**: M-Pesa, Pesapal integration
- **Real-time**: WebSocket, Server-Sent Events
- **Deployment**: Render.com compatible

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL database
- M-Pesa/Pesapal credentials (for payment processing)
- Modern web browser with WebSocket support

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd BlueSpace-Restaurants
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Configure database**
   ```bash
   # Set DATABASE_URL in your environment
   export DATABASE_URL="postgresql://username:password@localhost/bluespace_restaurants"
   ```

5. **Run database migrations**
   ```bash
   flask db upgrade
   ```

6. **Start the application**
   ```bash
   python app.py
   ```

## ⚙️ Configuration

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://username:password@localhost/bluespace_restaurants

# Flask
SECRET_KEY=your-secret-key-here
FLASK_ENV=production

# Payment Processing
MPESA_CONSUMER_KEY=your-mpesa-consumer-key
MPESA_CONSUMER_SECRET=your-mpesa-consumer-secret
PESAPAL_CONSUMER_KEY=your-pesapal-consumer-key
PESAPAL_CONSUMER_SECRET=your-pesapal-consumer-secret

# Hardware Notifications (optional)
SIMULATION_MODE=true
```

### Database Setup

The application uses PostgreSQL with the following key tables:
- `users` - Restaurant owners and staff
- `orders` - Order management with status tracking
- `menu_items` - Menu items with stock management
- `categories` - Menu organization
- `subscriptions` - Payment subscriptions

## 📱 Usage

### For Restaurant Owners

1. **Register and Login**
   - Create your restaurant account
   - Set up payment methods and contact information

2. **Menu Management**
   - Add menu items with categories
   - Set prices and stock levels
   - Generate QR codes for customer access

3. **Order Management**
   - Monitor real-time orders
   - Update order statuses smoothly
   - Handle payment confirmations
   - Track delivery orders

4. **Analytics**
   - View daily revenue and order statistics
   - Export reports for business analysis
   - Monitor performance metrics

### For Customers

1. **Access Menu**
   - Scan QR code or visit restaurant URL
   - Browse menu by categories
   - Add items to cart

2. **Place Order**
   - Select items and quantities
   - Add special instructions
   - Choose payment method
   - Complete order

3. **Track Order**
   - Real-time status updates
   - Payment confirmation
   - Delivery tracking (if applicable)

## 🔄 Order Status Flow

### Automated Flow
```
new → pending → paid → preparing → ready → delivered
```

### Manual Payment Flow
```
new → pending_confirmation → paid → preparing → ready → delivered
```

### Status Descriptions
- **new**: Order just created
- **pending**: Awaiting payment (auto-transition after 10 seconds)
- **pending_confirmation**: Manual payment awaiting confirmation
- **paid**: Payment received, ready for preparation
- **preparing**: Order being prepared
- **ready**: Order ready for pickup/delivery
- **delivered**: Order completed
- **cancelled**: Order cancelled (restores stock)

## 🔧 API Endpoints

### Order Management
- `GET /orders` - View all orders
- `POST /update_order_status/<order_id>` - Update order status
- `POST /api/order/<order_id>/confirm-payment` - Confirm manual payment
- `GET /order-updates` - Real-time order updates (SSE)

### Menu Management
- `GET /add_menu_item` - Add new menu item
- `POST /update_stock` - Update item stock
- `GET /menu-updates` - Real-time menu updates

### Payment Processing
- `POST /process-payment` - Process payment
- `POST /confirm-manual-payment/<order_id>` - Confirm manual payment
- `GET /payment-status/<order_id>` - Check payment status

### Hardware Notifications
- **Automatic notifications** for new orders, ready orders, and payments
- **Configurable patterns** (blink, pulse, solid) with custom durations
- **Priority-based processing** ensuring important notifications are handled first
- **Rate limiting** to prevent notification spam
- **Simulation mode** for development and testing

## 🚀 Deployment

### Render.com Deployment

1. **Connect your repository** to Render
2. **Create a new Web Service**
3. **Configure environment variables**
4. **Set build command**: `pip install -r requirements.txt`
5. **Set start command**: `gunicorn app:app`

### Environment Variables for Production

```env
DATABASE_URL=postgresql://...
SECRET_KEY=your-production-secret-key
FLASK_ENV=production
SIMULATION_MODE=false
```

## 🐛 Troubleshooting

### Common Issues

1. **Order Status Not Updating**
   - Check WebSocket connections
   - Verify database connectivity
   - Review order update logs

2. **Payment Processing Issues**
   - Verify payment credentials
   - Check callback URLs
   - Review payment logs

3. **Real-time Updates Not Working**
   - Ensure WebSocket support
   - Check browser console for errors
   - Verify SocketIO configuration

4. **Hardware Notifications Not Working**
   - Check GPIO permissions (Raspberry Pi)
   - Verify hardware connections
   - Test in simulation mode first
   - Review hardware_notifier.log

### Logs and Debugging

The application provides comprehensive logging:
- Order status changes
- Payment processing
- Real-time updates
- Hardware notifications
- Error tracking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## 🔄 Changelog

### Latest Updates
- **Optimized order status flow** with duplicate prevention
- **Enhanced real-time updates** with better performance
- **Improved payment processing** workflow
- **Professional hardware notification system** with queuing and rate limiting
- **Better error handling** and logging
- **Memory optimization** for tracking systems

---

**BlueSpace Restaurants** - Streamlining restaurant operations with modern technology 🍽️✨