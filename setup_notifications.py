#!/usr/bin/env python3
"""
Quick setup script for the notification system.
This script will create the database tables and add some sample notifications.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Notification, User
from datetime import datetime, timedelta, timezone
UTC = timezone.utc  # Compatibility alias for Python < 3.11

def setup_notification_system():
    """Set up the notification system with tables and sample data."""
    with app.app_context():
        try:
            print("🔔 Setting up BlueSpace Notification System...")
            print("=" * 50)
            
            # Create tables
            print("📊 Creating notification tables...")
            db.create_all()
            print("✅ Tables created successfully!")
            
            # Check if we have any users
            users = User.query.filter(User.is_admin == False).all()
            if not users:
                print("⚠️  No restaurant users found. Creating sample notifications anyway...")
            
            # Create sample notifications
            print("📝 Creating sample notifications...")
            
            sample_notifications = [
                {
                    'title': 'Welcome to BlueSpace Restaurants!',
                    'message': 'Thank you for joining our platform. We\'re excited to help you grow your business with our digital menu system.',
                    'notification_type': 'info',
                    'priority': 'normal',
                    'is_global': True
                },
                {
                    'title': 'System Update Available',
                    'message': 'A new system update is available with improved performance and new features. Please restart your application when convenient.',
                    'notification_type': 'update',
                    'priority': 'normal',
                    'is_global': True
                },
                {
                    'title': 'New Feature: Smart Kitchen Integration',
                    'message': 'We\'ve added a new Smart Kitchen feature that helps you manage orders more efficiently. Check it out in your dashboard!',
                    'notification_type': 'feature',
                    'priority': 'high',
                    'is_global': True
                },
                {
                    'title': 'Payment System Enhanced',
                    'message': 'We\'ve improved the payment processing system for faster and more reliable transactions.',
                    'notification_type': 'success',
                    'priority': 'normal',
                    'is_global': True
                }
            ]
            
            created_count = 0
            for notification_data in sample_notifications:
                # Check if notification already exists
                existing = Notification.query.filter_by(
                    title=notification_data['title'],
                    is_global=True
                ).first()
                
                if not existing:
                    notification = Notification(
                        title=notification_data['title'],
                        message=notification_data['message'],
                        notification_type=notification_data['notification_type'],
                        priority=notification_data['priority'],
                        is_global=notification_data['is_global'],
                        created_by=1,  # Assuming admin user ID 1
                        expires_at=datetime.now(UTC) + timedelta(days=30)  # Expire in 30 days
                    )
                    db.session.add(notification)
                    created_count += 1
            
            # Create a targeted notification for the first restaurant if available
            if users:
                targeted_notification = Notification(
                    title='Personalized Welcome',
                    message=f'Welcome {users[0].restaurant_name}! We\'re here to help you succeed with your digital menu.',
                    notification_type='info',
                    priority='normal',
                    is_global=False,
                    target_restaurant_id=users[0].id,
                    created_by=1
                )
                db.session.add(targeted_notification)
                created_count += 1
            
            db.session.commit()
            
            print(f"✅ Created {created_count} sample notifications!")
            print("\n📋 Sample notifications created:")
            for notification_data in sample_notifications:
                print(f"   - {notification_data['title']} ({notification_data['notification_type']})")
            if users:
                print(f"   - Personalized Welcome (targeted to {users[0].restaurant_name})")
            
            print("\n🎉 Notification system setup complete!")
            print("\n📖 Next steps:")
            print("1. Restart your Flask application")
            print("2. Log in as a restaurant user to see the notification bell")
            print("3. Log in as admin to manage notifications at /admin/notifications")
            print("4. Create new notifications through the admin panel")
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up notification system: {e}")
            return False

if __name__ == "__main__":
    success = setup_notification_system()
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("The notification bell system is now ready to use.")
    else:
        print("\n💥 Setup failed.")
        sys.exit(1)
