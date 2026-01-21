# Notification Table Fix

## Issue
The app was crashing with error:
```
relation "notification" does not exist
```

This happened because the notification tables haven't been created in the database yet.

## Fix Applied
✅ Updated notification API endpoints to gracefully handle missing tables:
- `/api/notifications` - Returns empty notifications if table doesn't exist
- `/api/notifications/<id>/read` - Returns 503 if table doesn't exist
- `/api/notifications/mark-all-read` - Returns 503 if table doesn't exist

The app will now work without crashing, but notifications won't be available until tables are created.

## To Enable Notifications

### Option 1: Quick Setup (Recommended)
```bash
python create_notification_tables.py
```

### Option 2: Using Alembic Migration
```bash
# Create migration
flask db migrate -m "Add notification system tables"

# Apply migration
flask db upgrade
```

## Verification
After creating tables, you can verify they exist:
```python
from app import app, db
from sqlalchemy import inspect

with app.app_context():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print('notification' in tables)  # Should be True
    print('notification_read' in tables)  # Should be True
```

## Current Status
- ✅ App no longer crashes when notification table is missing
- ✅ Notification endpoints return empty/graceful responses
- ⚠️ Notification features won't work until tables are created
- 📝 Tables can be created anytime without affecting existing functionality

