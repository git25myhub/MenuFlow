# 🔔 BlueSpace Restaurant Notification System

A comprehensive notification system for BlueSpace Restaurants that allows administrators to send professional notifications to restaurants about system updates, new features, and important announcements.

## ✨ Features

### For Restaurants
- **Notification Bell**: A prominent bell icon in the navbar showing unread notification count
- **Real-time Updates**: Notifications refresh automatically every 30 seconds
- **Professional Display**: Clean, organized notification dropdown with different types and priorities
- **Mark as Read**: Individual notifications can be marked as read
- **Mark All Read**: Bulk action to mark all notifications as read
- **Visual Indicators**: Different icons and colors for different notification types

### For Administrators
- **Create Notifications**: Full admin panel to create and manage notifications
- **Targeting Options**: Send to all restaurants (global) or specific restaurants
- **Notification Types**: Info, Warning, Success, Error, System Update, New Feature
- **Priority Levels**: Low, Normal, High, Urgent
- **Expiration**: Set automatic expiration dates for notifications
- **Toggle Active**: Activate/deactivate notifications without deleting them
- **Delete**: Remove notifications permanently

## 🚀 Quick Start

### 1. Create Database Tables
```bash
python create_notification_tables.py
```

### 2. Test the System
```bash
python test_notification_system.py
```

### 3. Access Admin Panel
- Log in as admin
- Navigate to `/admin/notifications`
- Create your first notification

## 📋 Database Schema

### Notification Table
```sql
- id: Primary key
- title: Notification title (max 255 chars)
- message: Notification content (text)
- notification_type: 'info', 'warning', 'success', 'error', 'update', 'feature'
- priority: 'low', 'normal', 'high', 'urgent'
- is_global: Boolean - true for all restaurants, false for specific
- target_restaurant_id: Restaurant ID (if not global)
- created_by: Admin user ID who created it
- created_at: Creation timestamp
- expires_at: Optional expiration date
- is_active: Boolean - active/inactive status
```

### NotificationRead Table
```sql
- id: Primary key
- notification_id: Foreign key to notification
- user_id: Foreign key to user (restaurant)
- read_at: Timestamp when marked as read
- Unique constraint on (notification_id, user_id)
```

## 🎯 API Endpoints

### For Restaurants
- `GET /api/notifications` - Get all notifications for current user
- `POST /api/notifications/{id}/read` - Mark notification as read
- `POST /api/notifications/mark-all-read` - Mark all notifications as read

### For Administrators
- `GET /admin/notifications` - Admin panel for managing notifications
- `GET /admin/notifications/create` - Create new notification form
- `POST /admin/notifications/create` - Create notification
- `POST /admin/notifications/{id}/toggle` - Toggle notification active status
- `POST /admin/notifications/{id}/delete` - Delete notification

## 🎨 Notification Types & Icons

| Type | Icon | Color | Use Case |
|------|------|-------|----------|
| Info | `fa-info-circle` | Blue | General information |
| Warning | `fa-exclamation-triangle` | Yellow | Important notices |
| Success | `fa-check-circle` | Green | Positive updates |
| Error | `fa-times-circle` | Red | Critical issues |
| Update | `fa-sync-alt` | Blue | System updates |
| Feature | `fa-star` | Purple | New features |

## 🎨 Priority Levels & Colors

| Priority | Color | Use Case |
|----------|-------|----------|
| Low | Gray | Minor updates |
| Normal | Blue | Regular announcements |
| High | Yellow | Important notices |
| Urgent | Red | Critical alerts |

## 💡 Usage Examples

### Creating a System Update Notification
```python
notification = Notification(
    title="System Update v2.1.0",
    message="We've released a new version with improved performance and bug fixes.",
    notification_type="update",
    priority="normal",
    is_global=True,
    expires_at=datetime.now(UTC) + timedelta(days=7)
)
```

### Creating a Targeted Feature Announcement
```python
notification = Notification(
    title="New Analytics Dashboard",
    message="Check out the new analytics features in your admin panel.",
    notification_type="feature",
    priority="high",
    is_global=False,
    target_restaurant_id=restaurant_id
)
```

## 🔧 Customization

### Adding New Notification Types
1. Update the `notification_type` enum in the model
2. Add corresponding CSS classes in `base.html`
3. Add icons in `notifications.js`
4. Update the admin form options

### Styling Customization
The notification system uses CSS custom properties for theming:
- `--bluespace-blue`: Primary blue color
- `--bluespace-light-blue`: Accent blue
- `--border`: Border color
- `--muted`: Background for hover states

## 🐛 Troubleshooting

### Notifications Not Showing
1. Check if user is authenticated
2. Verify notification is active (`is_active = True`)
3. Check expiration date
4. Ensure user has access (global or targeted)

### Bell Icon Not Appearing
1. Check if user is logged in
2. Verify JavaScript is loading
3. Check browser console for errors

### Admin Panel Not Working
1. Ensure user has admin privileges
2. Check database tables exist
3. Verify all templates are in place

## 📱 Mobile Responsiveness

The notification system is fully responsive:
- Bell icon scales properly on mobile
- Dropdown adjusts to screen width
- Touch-friendly buttons and interactions
- Optimized for both desktop and mobile use

## 🔒 Security Features

- **Authentication Required**: All endpoints require login
- **Admin Authorization**: Admin functions require admin privileges
- **Input Validation**: All inputs are validated and sanitized
- **SQL Injection Protection**: Uses SQLAlchemy ORM
- **XSS Protection**: HTML content is properly escaped

## 🚀 Performance Features

- **Auto-refresh**: Notifications update every 30 seconds
- **Efficient Queries**: Optimized database queries
- **Lazy Loading**: JavaScript loads only when needed
- **Caching**: Notification data cached in browser
- **Minimal DOM Updates**: Only updates changed elements

## 📈 Future Enhancements

- **Email Notifications**: Send email copies of important notifications
- **Push Notifications**: Browser push notifications
- **Notification Templates**: Pre-built notification templates
- **Scheduled Notifications**: Send notifications at specific times
- **Notification Analytics**: Track read rates and engagement
- **Rich Text**: Support for formatted notification content
- **Attachments**: Support for images and documents

## 🤝 Contributing

To contribute to the notification system:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This notification system is part of the BlueSpace Restaurants project and follows the same licensing terms.

---

**Need Help?** Contact the development team or check the main project documentation for additional support.
