/**
 * Notification Bell System
 * Handles loading, displaying, and managing notifications for restaurants
 */

class NotificationSystem {
    constructor() {
        this.notifications = [];
        this.unreadCount = 0;
        this.refreshInterval = 30000; // 30 seconds
        this.isLoading = false;
        
        this.init();
    }
    
    init() {
        // Load notifications on page load
        this.loadNotifications();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Set up auto-refresh
        this.setupAutoRefresh();
    }
    
    setupEventListeners() {
        // Mark all as read button
        const markAllReadBtn = document.getElementById('mark-all-read-btn');
        if (markAllReadBtn) {
            markAllReadBtn.addEventListener('click', () => this.markAllAsRead());
        }
        
        // Notification dropdown toggle
        const notificationDropdown = document.getElementById('notificationDropdown');
        if (notificationDropdown) {
            notificationDropdown.addEventListener('click', () => {
                if (!this.isLoading) {
                    this.loadNotifications();
                }
            });
        }
    }
    
    setupAutoRefresh() {
        // Refresh notifications every 30 seconds
        setInterval(() => {
            if (!this.isLoading) {
                this.loadNotifications();
            }
        }, this.refreshInterval);
    }
    
    async loadNotifications() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        
        try {
            const response = await fetch('/api/notifications');
            const data = await response.json();
            
            if (data.success) {
                this.notifications = data.notifications;
                this.unreadCount = data.unread_count;
                this.updateUI();
            } else {
                console.error('Failed to load notifications:', data.message);
                this.showError('Failed to load notifications');
            }
        } catch (error) {
            console.error('Error loading notifications:', error);
            this.showError('Error loading notifications');
        } finally {
            this.isLoading = false;
        }
    }
    
    updateUI() {
        this.updateBadge();
        this.updateNotificationsList();
        this.updateMarkAllButton();
    }
    
    updateBadge() {
        const badge = document.getElementById('notification-badge');
        if (badge) {
            if (this.unreadCount > 0) {
                badge.textContent = this.unreadCount;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        }
    }
    
    updateNotificationsList() {
        const list = document.getElementById('notifications-list');
        if (!list) return;
        
        if (this.notifications.length === 0) {
            list.innerHTML = `
                <div class="text-center p-3 text-muted">
                    <i class="fas fa-bell-slash fa-2x mb-2"></i>
                    <div>No notifications</div>
                </div>
            `;
            return;
        }
        
        const notificationsHtml = this.notifications.map(notification => {
            const typeClass = this.getTypeClass(notification.type);
            const priorityClass = this.getPriorityClass(notification.priority);
            const readClass = notification.is_read ? '' : 'fw-bold';
            const timeAgo = this.getTimeAgo(notification.created_at);
            
            return `
                <li class="notification-item ${readClass}" data-notification-id="${notification.id}">
                    <div class="dropdown-item-text p-3 border-bottom">
                        <div class="d-flex align-items-start">
                            <div class="me-2">
                                <i class="fas ${this.getTypeIcon(notification.type)} ${typeClass}"></i>
                            </div>
                            <div class="flex-grow-1">
                                <div class="d-flex justify-content-between align-items-start">
                                    <h6 class="mb-1 ${readClass}">${this.escapeHtml(notification.title)}</h6>
                                    <small class="text-muted">${timeAgo}</small>
                                </div>
                                <p class="mb-1 text-muted">${this.escapeHtml(notification.message)}</p>
                                <div class="d-flex justify-content-between align-items-center">
                                    <span class="badge ${priorityClass}">${notification.priority}</span>
                                    ${!notification.is_read ? '<button class="btn btn-sm btn-outline-primary mark-read-btn">Mark as read</button>' : ''}
                                </div>
                            </div>
                        </div>
                    </div>
                </li>
            `;
        }).join('');
        
        list.innerHTML = notificationsHtml;
        
        // Add event listeners to mark as read buttons
        list.querySelectorAll('.mark-read-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const notificationItem = e.target.closest('.notification-item');
                const notificationId = notificationItem.dataset.notificationId;
                this.markAsRead(notificationId);
            });
        });
    }
    
    updateMarkAllButton() {
        const markAllBtn = document.getElementById('mark-all-read-btn');
        if (markAllBtn) {
            if (this.unreadCount > 0) {
                markAllBtn.style.display = 'inline-block';
            } else {
                markAllBtn.style.display = 'none';
            }
        }
    }
    
    async markAsRead(notificationId) {
        try {
            const response = await fetch(`/api/notifications/${notificationId}/read`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update local state
                const notification = this.notifications.find(n => n.id == notificationId);
                if (notification) {
                    notification.is_read = true;
                    this.unreadCount = Math.max(0, this.unreadCount - 1);
                }
                
                // Update UI
                this.updateUI();
            } else {
                console.error('Failed to mark notification as read:', data.message);
            }
        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    }
    
    async markAllAsRead() {
        try {
            const response = await fetch('/api/notifications/mark-all-read', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update local state
                this.notifications.forEach(notification => {
                    notification.is_read = true;
                });
                this.unreadCount = 0;
                
                // Update UI
                this.updateUI();
            } else {
                console.error('Failed to mark all notifications as read:', data.message);
            }
        } catch (error) {
            console.error('Error marking all notifications as read:', error);
        }
    }
    
    getTypeClass(type) {
        const typeClasses = {
            'info': 'text-info',
            'warning': 'text-warning',
            'success': 'text-success',
            'error': 'text-danger',
            'update': 'text-primary',
            'feature': 'text-purple'
        };
        return typeClasses[type] || 'text-info';
    }
    
    getPriorityClass(priority) {
        const priorityClasses = {
            'low': 'bg-secondary',
            'normal': 'bg-primary',
            'high': 'bg-warning',
            'urgent': 'bg-danger'
        };
        return priorityClasses[priority] || 'bg-primary';
    }
    
    getTypeIcon(type) {
        const typeIcons = {
            'info': 'fa-info-circle',
            'warning': 'fa-exclamation-triangle',
            'success': 'fa-check-circle',
            'error': 'fa-times-circle',
            'update': 'fa-sync-alt',
            'feature': 'fa-star'
        };
        return typeIcons[type] || 'fa-bell';
    }
    
    getTimeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);
        
        if (diffInSeconds < 60) {
            return 'Just now';
        } else if (diffInSeconds < 3600) {
            const minutes = Math.floor(diffInSeconds / 60);
            return `${minutes}m ago`;
        } else if (diffInSeconds < 86400) {
            const hours = Math.floor(diffInSeconds / 3600);
            return `${hours}h ago`;
        } else {
            const days = Math.floor(diffInSeconds / 86400);
            return `${days}d ago`;
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    showError(message) {
        const list = document.getElementById('notifications-list');
        if (list) {
            list.innerHTML = `
                <div class="text-center p-3 text-danger">
                    <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
                    <div>${message}</div>
                </div>
            `;
        }
    }
}

// Initialize notification system when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if user is authenticated
    if (typeof CURRENT_USER_ID !== 'undefined' && CURRENT_USER_ID) {
        window.notificationSystem = new NotificationSystem();
    }
});
