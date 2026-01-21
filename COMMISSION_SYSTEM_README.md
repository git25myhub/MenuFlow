# BlueSpace Restaurants - Commission System

## Overview

The commission system allows the platform to collect a percentage or fixed amount commission from each order processed through the BlueSpace Restaurants platform. This system is designed to be fair, transparent, and easy to manage for both platform administrators and restaurant owners.

## Features

### For Restaurant Owners
- **Commission Dashboard**: View commission summary, pending bills, and recent transactions
- **Payment Instructions**: Clear instructions on how to pay commission via M-Pesa
- **Transparent Calculations**: See exactly how commission is calculated for each order
- **Payment History**: Track all commission payments and bills

### For Platform Administrators
- **Commission Settings**: Configure commission rates for each restaurant
- **Commission Bills**: Manage and track commission payments
- **Commission Reports**: Generate detailed analytics and reports
- **Payment Confirmation**: Confirm commission payments received from restaurants

## Commission Structure

### Commission Types
1. **Percentage-based**: Commission calculated as a percentage of order value (e.g., 5%)
2. **Fixed Amount**: Fixed commission amount per order regardless of value (e.g., 20 KES)

### Commission Rules
- **Minimum Order Amount**: No commission on orders below this threshold (default: 50 KES)
- **Maximum Commission**: Cap on commission amount per order (default: 500 KES)
- **Commission Calculation**: Applied when order is marked as paid

### Default Settings
- **Default Commission Rate**: 5% of order value
- **Minimum Order Amount**: 50 KES
- **Maximum Commission**: 500 KES per order
- **Currency**: KES (Kenyan Shillings)

## Database Schema

### New Tables
1. **commission_config**: Restaurant-specific commission settings
2. **commission_transaction**: Individual commission calculations per order
3. **commission_bill**: Monthly commission bills for restaurants
4. **commission_payout**: Platform payout records

### Updated Tables
- **order**: Added commission_amount and commission_status columns
- **platform_settings**: Added commission-related platform settings

## Installation & Setup

### 1. Run Database Migration
```bash
python create_commission_tables.py
```

This script will:
- Create all commission-related database tables
- Add commission columns to existing orders table
- Initialize platform settings with default values
- Create default commission configurations for existing restaurants

### 2. Restart Application
```bash
# Restart your Flask application
python app.py
```

### 3. Access Commission Features
- **Restaurant Dashboard**: `/commission-dashboard`
- **Admin Settings**: `/admin/commission-settings`
- **Commission Bills**: `/admin/commission-bills`
- **Commission Reports**: `/admin/commission-reports`

## Usage Guide

### For Restaurant Owners

#### Viewing Commission Dashboard
1. Log in to your restaurant account
2. Click "Commission" in the navigation menu
3. View your commission summary, pending bills, and recent transactions

#### Paying Commission
1. Check your pending commission bills on the dashboard
2. Send payment to the platform M-Pesa number shown
3. Use the provided reference format (e.g., REST123_2024_01)
4. Keep payment confirmation for your records
5. Contact admin to confirm payment has been received

### For Platform Administrators

#### Configuring Commission Rates
1. Access `/admin/commission-settings`
2. Select a restaurant from the dropdown
3. Choose commission type (percentage or fixed)
4. Set commission rate and limits
5. Save configuration

#### Managing Commission Bills
1. Access `/admin/commission-bills`
2. View pending, overdue, and paid bills
3. Click "Generate Bill" to create monthly bills
4. Click "Confirm Payment" when restaurants pay commission

#### Generating Reports
1. Access `/admin/commission-reports`
2. Select date range for analysis
3. View platform-wide commission summary
4. Analyze restaurant-specific commission data

## Commission Calculation Examples

### Example 1: Percentage-based Commission
- **Order Value**: 1,000 KES
- **Commission Rate**: 5%
- **Commission Amount**: 50 KES
- **Restaurant Receives**: 950 KES

### Example 2: Fixed Commission
- **Order Value**: 800 KES
- **Fixed Commission**: 20 KES
- **Commission Amount**: 20 KES
- **Restaurant Receives**: 780 KES

### Example 3: With Minimum Order Amount
- **Order Value**: 30 KES
- **Minimum Order**: 50 KES
- **Commission Amount**: 0 KES (below minimum)
- **Restaurant Receives**: 30 KES

### Example 4: With Maximum Commission Cap
- **Order Value**: 15,000 KES
- **Commission Rate**: 5%
- **Calculated Commission**: 750 KES
- **Maximum Commission**: 500 KES
- **Final Commission**: 500 KES
- **Restaurant Receives**: 14,500 KES

## Payment Collection Process

### For Manual Payment Mode
1. Restaurant confirms order payment received
2. System calculates commission automatically
3. Commission is added to restaurant's monthly bill
4. Restaurant pays commission via M-Pesa to platform
5. Admin confirms payment in the system

### For STK Push Mode
1. Customer pays via M-Pesa STK Push
2. Platform automatically deducts commission
3. Restaurant receives order amount minus commission
4. Commission is recorded in the system

## Commission Bill Generation

### Monthly Bills
- Bills are generated monthly for each restaurant
- Due date is set to 15th of the following month
- Bills include all commission transactions for the period
- Restaurants can view their bills on the commission dashboard

### Bill Status
- **Pending**: Bill generated, payment not yet received
- **Overdue**: Payment past due date
- **Paid**: Payment confirmed by admin

## API Endpoints

### Restaurant Endpoints
- `GET /commission-dashboard` - Restaurant commission dashboard
- `POST /confirm-manual-payment/<order_id>` - Confirm manual payment (includes commission calculation)

### Admin Endpoints
- `GET /admin/commission-settings` - Commission configuration interface
- `POST /admin/commission-settings` - Update commission settings
- `GET /admin/commission-bills` - Commission bills management
- `POST /admin/confirm-commission-payment/<bill_id>` - Confirm commission payment
- `GET /admin/commission-reports` - Commission analytics and reports
- `GET /admin/generate-commission-bill/<restaurant_id>` - Generate monthly bill
- `GET /admin/commission-bill/<bill_id>` - View bill details

## Configuration

### Platform Settings
- **Platform M-Pesa Number**: 254769950059 (default)
- **Default Commission Rate**: 5% (default)
- **Commission Currency**: KES (default)

### Restaurant Settings
Each restaurant can have custom commission settings:
- Commission type (percentage or fixed)
- Commission rate
- Minimum order amount
- Maximum commission cap

## Security & Permissions

### Access Control
- **Restaurant Owners**: Can view their own commission data
- **Admin Users**: Can access all commission management features
- **Regular Users**: No access to commission features

### Data Protection
- Commission data is stored securely in the database
- Payment confirmations require admin verification
- All commission transactions are logged and auditable

## Troubleshooting

### Common Issues

#### Commission Not Calculating
- Check if restaurant has commission configuration
- Verify order amount meets minimum threshold
- Ensure order status is 'paid'

#### Payment Confirmation Issues
- Verify payment reference matches expected format
- Check that amount received matches bill amount
- Ensure admin has proper permissions

#### Database Migration Errors
- Backup existing database before migration
- Check database permissions
- Verify all required tables exist

### Support
For technical support or questions about the commission system, please contact the platform administrator.

## Future Enhancements

### Planned Features
- Automated commission reminders via SMS/email
- Integration with additional payment methods
- Advanced commission analytics and forecasting
- Commission tier system based on restaurant performance
- Automated commission payouts to platform account

### Customization Options
- Custom commission calculation formulas
- Seasonal commission rate adjustments
- Restaurant-specific commission promotions
- Commission exemption periods for new restaurants

## License

This commission system is part of the BlueSpace Restaurants platform and is proprietary software.

---

**Version**: 1.0  
**Last Updated**: December 2024  
**Author**: BlueSpace Restaurants Development Team 