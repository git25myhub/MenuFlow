// Dashboard page JavaScript

// Add Socket.IO client initialization at the top
// Assumes <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script> is included in the HTML
if (!window.socket) {
    window.socket = io({ transports: ['websocket'] });
}
// Join dashboard and menu rooms for real-time updates
if (typeof CURRENT_USER_ID !== 'undefined') {
    window.socket.emit('join_dashboard', { user_id: CURRENT_USER_ID });
    window.socket.emit('join_menu', { user_id: CURRENT_USER_ID });
}
// Listen for dashboard updates
window.socket.on('dashboard_update', function(data) {
    console.log('Received dashboard update:', data);
    // Update pending dine-in orders
    const pendingDineInElem = document.getElementById('pending-dine-in');
    if (pendingDineInElem) {
        pendingDineInElem.textContent = data.pending_dine_in || 0;
    }
    // Update pending delivery orders
    const pendingDeliveryElem = document.getElementById('pending-delivery');
    if (pendingDeliveryElem) {
        pendingDeliveryElem.textContent = data.pending_delivery || 0;
    }
    // Update delivered orders
    const deliveredOrdersElem = document.getElementById('delivered-orders');
    if (deliveredOrdersElem) {
        deliveredOrdersElem.textContent = data.delivered_orders || 0;
    }
    // Update today's revenue
    const todayRevenueElem = document.getElementById('today-revenue');
    if (todayRevenueElem) {
        todayRevenueElem.textContent = data.today_revenue || 0;
    }
    // Update total orders
    const totalOrdersElem = document.getElementById('total-orders');
    if (totalOrdersElem) {
        totalOrdersElem.textContent = data.total_orders || 0;
    }
});

// Listen for menu/stock updates
socket.on('menu_update', function(data) {
    console.log('[Socket.IO] Menu/Stock update:', data);
    if (data.type === 'stock_update') {
        // Update stock cell in DOM
        const stockCell = document.getElementById(`stock-${data.item_id}`);
        if (stockCell) {
            stockCell.textContent = data.new_stock;
            showToast('success', `Stock updated for item #${data.item_id}`);
        }
    } else if (data.type === 'menu_add') {
        // Add new menu item row to the menu table
        const menuTable = document.getElementById('menuTable');
        if (menuTable && data.item) {
            // Check if row already exists
            if (!document.getElementById(`menu-row-${data.item.id}`)) {
                const row = document.createElement('tr');
                row.id = `menu-row-${data.item.id}`;
                row.innerHTML = `
                    <td>${data.item.id}</td>
                    <td>${data.item.name}</td>
                    <td>${data.item.description || ''}</td>
                    <td>${data.item.price}</td>
                    <td id="stock-${data.item.id}">${data.item.stock}</td>
                    <td><img src="${data.item.image_url || ''}" alt="" width="40" height="40"></td>
                    <td>
                        <!-- Action buttons: You may want to re-render or add event listeners if needed -->
                        <button class="btn btn-danger btn-sm delete-btn" data-item-id="${data.item.id}">Delete</button>
                    </td>
                `;
                menuTable.querySelector('tbody')?.appendChild(row);
                showToast('success', `New menu item added: ${data.item.name}`);
            }
        }
    } else if (data.type === 'menu_delete') {
        // Remove menu item row from the menu table
        const row = document.getElementById(`menu-row-${data.item_id}`);
        if (row) {
            row.remove();
            showToast('success', `Menu item #${data.item_id} deleted`);
        }
    } else if (data.type === 'menu_edit') {
        // Update menu item row in the menu table
        const row = document.getElementById(`menu-row-${data.item.id}`);
        if (row) {
            row.innerHTML = `
                <td>${data.item.id}</td>
                <td>${data.item.name}</td>
                <td>${data.item.description || ''}</td>
                <td>${data.item.price}</td>
                <td id="stock-${data.item.id}">${data.item.stock}</td>
                <td><img src="${data.item.image_url || ''}" alt="" width="40" height="40"></td>
                <td>
                    <!-- Action buttons: You may want to re-render or add event listeners if needed -->
                    <button class="btn btn-danger btn-sm delete-btn" data-item-id="${data.item.id}">Delete</button>
                </td>
            `;
            showToast('success', `Menu item updated: ${data.item.name}`);
        }
    }
});

// Global variables
let currentDeleteItemId = null;
let deleteModal = null;
let stockModal = null;

// Function to show toast notifications
function showToast(type, message) {
    try {
        // Ensure toast container exists
        const toastContainer = document.querySelector('#toastContainer');
        if (!toastContainer) {
            const container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'position-fixed top-0 end-0 p-3';
            container.style.zIndex = '1080';
            document.body.appendChild(container);
        }

        // Create toast element
        const toastElement = document.createElement('div');
        toastElement.className = `toast ${type === 'success' ? 'bg-success' : 'bg-danger'} text-white`;
        toastElement.innerHTML = `
            <div class="toast-header">
                <strong class="me-auto">${type === 'success' ? 'Success' : 'Error'}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        // Add toast to container
        document.getElementById('toastContainer').appendChild(toastElement);

        // Initialize and show toast
        const toast = new bootstrap.Toast(toastElement, {
            delay: 3000
        });
        toast.show();

        // Clean up after toast is hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    } catch (error) {
        console.error('Error showing toast:', error);
    }
}

// Function to confirm delete action
function confirmDelete(itemId) {
    currentDeleteItemId = itemId;
    deleteModal.show();
}

// Function to show/hide loading state
function toggleLoadingState(button, show) {
    if (!button) return;
    
    const originalContent = button.innerHTML;
    if (show) {
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        button.disabled = true;
    } else {
        button.innerHTML = originalContent;
        button.disabled = false;
    }
}

// Function to handle menu item deletion
function deleteMenuItem(itemId) {
    try {
        // Get CSRF token from meta tag
        const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
        if (!csrfToken) {
            console.error('CSRF token not found');
            showToast('error', 'CSRF token not found. Please reload the page.');
            return;
        }

        // Show loading state
        const button = document.querySelector(`[data-item-id="${itemId}"]`);
        if (button) {
            const originalContent = button.innerHTML;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';
            button.disabled = true;
        }

        fetch(`/delete_menu_item/${itemId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                // Always try to get JSON response first
                return response.json()
                    .catch(() => {
                        // If JSON parsing fails, get text response
                        return response.text()
                            .then(text => {
                                try {
                                    // Try parsing as JSON one more time
                                    return JSON.parse(text);
                                } catch (e) {
                                    // If still not JSON, return plain text
                                    return { error: text || 'Request failed' };
                                }
                            });
                    })
                    .then(data => {
                        throw new Error(data.error || data.message || 'Request failed');
                    });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Close modal
                if (deleteModal) {
                    deleteModal.close();
                }
                showToast('success', 'Menu item deleted successfully!');
                // Remove deleted menu item from DOM
                const deletedRow = document.querySelector(`[data-item-id="${itemId}"]`);
                if (deletedRow) deletedRow.remove();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('error', error.message || 'Failed to delete menu item');
            // Reset button state
            if (button) {
                button.innerHTML = originalContent;
                button.disabled = false;
            }
        });
    } catch (error) {
        console.error('Error in deleteMenuItem:', error);
        showToast('error', 'An unexpected error occurred');
    }
}

// Function to update menu item stock
function updateStock() {
    const itemId = document.getElementById('stock-item-id').value;
    const newStock = document.getElementById('stock-amount').value;
    
    if (!itemId || !newStock) {
        showToast('error', 'Please fill in all fields');
        return;
    }

    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
        if (!csrfToken) {
            showToast('error', 'CSRF token not found. Please reload the page.');
            return;
        }

        fetch('/update_stock', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin',
            body: JSON.stringify({
                item_id: itemId,
                new_stock: newStock
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('success', 'Stock updated successfully!');
                // Close modal
                const modal = document.getElementById('stockModal');
                if (modal) {
                    modal.close();
                }
                // Refresh menu items
                const stockCell = document.getElementById(`stock-${itemId}`);
if (stockCell) stockCell.textContent = newStock;
            } else {
                showToast('error', data.message || 'Failed to update stock');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('error', error.message || 'Failed to update stock');
        });
    } catch (error) {
        console.error('Error in updateStock:', error);
        showToast('error', 'An unexpected error occurred');
    }
}

// Function to initialize the dashboard
function initializeDashboard() {
    try {
        // Initialize delete modal
        const deleteModalElement = document.getElementById('deleteModal');
        if (deleteModalElement) {
            deleteModal = new bootstrap.Modal(deleteModalElement);
        }

        // Initialize stock modal
        const stockModalElement = document.getElementById('stockModal');
        if (stockModalElement) {
            stockModal = new bootstrap.Modal(stockModalElement);
            
            // Add click handlers for stock management buttons
            document.querySelectorAll('.edit-stock-btn').forEach(button => {
                button.addEventListener('click', function() {
                    const itemId = this.dataset.itemId;
                    const itemName = this.closest('tr').querySelector('td:nth-child(2)').textContent;
                    const currentStock = this.closest('tr').querySelector('td:nth-child(5)').textContent;
                    
                    const stockItemId = document.getElementById('stockItemId');
                    const newStock = document.getElementById('newStock');
                    const stockModalLabel = document.querySelector('.modal-title');
                    
                    if (!stockItemId || !newStock || !stockModalLabel) {
                        console.error('Missing stock modal form elements');
                        showToast('error', 'Stock modal form elements not found. Please reload the page.');
                        return;
                    }
                    
                    stockItemId.value = itemId;
                    newStock.value = currentStock;
                    stockModalLabel.textContent = `Update Stock for ${itemName}`;
                    
                    stockModal.show();
                });
            });
        }

        // Initialize delete confirmation
        const deleteConfirmBtn = document.getElementById('deleteConfirmBtn');
        if (deleteConfirmBtn) {
            deleteConfirmBtn.addEventListener('click', function() {
                if (currentDeleteItemId) {
                    deleteMenuItem(currentDeleteItemId);
                }
            });
        } else {
            console.error('Delete confirm button not found');
            showToast('error', 'Delete functionality not available. Please reload the page.');
        }

        // Initialize real-time updates
        // initializeDashboardUpdates(); // This function is now handled by Socket.IO
    } catch (error) {
        console.error('Error initializing dashboard:', error);
        showToast('error', 'Failed to initialize dashboard. Please reload the page.');
    }
}

// Initialize the dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', initializeDashboard);

// Function to update order status
function updateOrderStatus(orderId, newStatus) {
    console.log('updateOrderStatus called with:', orderId, newStatus);
    
    // Show loading state
    const button = document.querySelector(`button[onclick*="updateOrderStatus(${orderId}")"]`);
    if (!button) {
        console.error('Button not found for order:', orderId);
        return;
    }
    
    const originalContent = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
    button.disabled = true;

    // Get CSRF token from meta tag or cookie
    let csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    if (!csrfToken) {
        const cookie = document.cookie.split('; ').find(row => row.startsWith('csrf_token='));
        csrfToken = cookie ? cookie.split('=')[1] : '';
    }

    if (!csrfToken) {
        console.error('CSRF token not found');
        button.innerHTML = originalContent;
        button.disabled = false;
        showToast('error', 'CSRF token not found. Please reload the page.');
        return;
    }

    console.log('CSRF token:', csrfToken);

    fetch(`/update_order_status/${orderId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ status: newStatus })
    })
    .then(response => {
        console.log('Response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
        if (data.success) {
            // Update UI
            button.innerHTML = `<i class="fas fa-check"></i> ${newStatus.charAt(0).toUpperCase() + newStatus.slice(1)}`;
            button.classList.remove('btn-primary', 'btn-success', 'btn-info', 'btn-danger');
            
            switch(newStatus) {
                case 'paid':
                    button.classList.add('btn-success');
                    break;
                case 'preparing':
                    button.classList.add('btn-primary');
                    break;
                case 'ready':
                    button.classList.add('btn-info');
                    break;
                case 'delivered':
                    button.classList.add('btn-success');
                    break;
                case 'cancelled':
                    button.classList.add('btn-danger');
                    break;
            }
            
            // Update order status badge
            const statusBadge = document.querySelector(`.order-status-badge[data-order-id="${orderId}"]`);
            if (statusBadge) {
                statusBadge.textContent = newStatus.charAt(0).toUpperCase() + newStatus.slice(1);
                
                // Update badge color
                switch(newStatus) {
                    case 'pending':
                        statusBadge.classList.add('bg-warning', 'text-dark');
                        break;
                    case 'paid':
                        statusBadge.classList.add('bg-info', 'text-dark');
                        break;
                    case 'preparing':
                        statusBadge.classList.add('bg-primary');
                        break;
                    case 'ready':
                        statusBadge.classList.add('bg-success');
                        break;
                    case 'cancelled':
                        statusBadge.classList.add('bg-danger');
                        break;
                }
            }
            
            showToast('success', 'Order status updated successfully!');
            
            // Do not reload; UI will update via SSE or DOM manipulation
            // Optionally, show a toast or update the UI here if needed
            showToast('success', 'Order status updated successfully!');
        } else {
            throw new Error(data.error || 'Failed to update order status');
        }
    })
    .catch(error => {
        console.error('Error updating order status:', error);
        // Restore button state
        button.innerHTML = originalContent;
        button.disabled = false;
        showToast('error', error.message || 'Failed to update order status');
    });
}

function deleteMenuItem(itemId) {
    try {
        // Get CSRF token from meta tag
        const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
        if (!csrfToken) {
            console.error('CSRF token not found');
            showToast('error', 'CSRF token not found. Please reload the page.');
            return;
        }

        // Show loading state
        const button = document.querySelector(`[data-item-id="${itemId}"]`);
        if (button) {
            const originalContent = button.innerHTML;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';
            button.disabled = true;
        }

        // Create JSON data
        const data = {
            csrf_token: csrfToken
        };

        fetch(`/delete_menu_item/${itemId}`, {
            method: 'POST',
            headers: {
                'X-CSRF-Token': csrfToken,
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin',
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                // First try to parse as JSON
                return response.json()
                    .then(data => {
                        throw new Error(data.error || data.message || 'Failed to delete menu item');
                    })
                    .catch(() => {
                        // If JSON parsing fails, get the text and throw it as error
                        return response.text()
                            .then(text => {
                                throw new Error(text || 'Request failed');
                            });
                    });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Close modal and refresh menu items
                if (deleteModal) {
                    deleteModal.hide();
                }
                showToast('success', data.message);
                // Refresh menu items
                const stockCell = document.getElementById(`stock-${itemId}`);
if (stockCell) stockCell.textContent = newStock;
            } else {
                throw new Error(data.error || 'Failed to delete menu item');
            }
        })
        .catch(error => {
            if (button) {
                toggleLoadingState(button, false);
            }
            console.error('Delete error:', error);
            showToast('error', error.message || 'Failed to delete menu item');
        });
    } catch (error) {
        console.error('Error in deleteMenuItem:', error);
        showToast('error', 'An unexpected error occurred. Please try again.');
    }
}

// Initialize real-time updates with enhanced error handling and reconnection logic
// This function is now handled by Socket.IO

function markOrderDelivered(orderId) {
    // Show loading state
    const button = document.querySelector(`[data-order-id="${orderId}"]`);
    const originalContent = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    button.disabled = true;

    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    if (!csrfToken) {
        showToast('error', 'CSRF token not found. Please reload the page.');
        return;
    }

    fetch(`/api/order/${orderId}/deliver`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Update UI with success state
            button.innerHTML = '<i class="fas fa-check"></i> Delivered';
            button.classList.remove('btn-primary');
            button.classList.add('btn-success');
            showToast('success', 'Order marked as delivered successfully!');
            
            // Update order status in the table if it exists
            const statusCell = document.querySelector(`.order-status-badge[data-order-id="${orderId}"]`);
            if (statusCell) {
                statusCell.textContent = 'Delivered';
                statusCell.classList.remove('badge-primary');
                statusCell.classList.add('badge-success');
            }
        } else {
            throw new Error(data.message || 'Failed to mark order as delivered');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        // Restore button state
        button.innerHTML = originalContent;
        button.disabled = false;
        showToast('error', error.message || 'An error occurred while processing your request');
    });
}

function showToast(type, message) {
    try {
        // Check if Bootstrap is loaded
        if (typeof bootstrap === 'undefined') {
            console.error('Bootstrap is not loaded');
            return;
        }

        // Get or create toast container
        let toastContainer = document.getElementById('toastContainer');
        if (!toastContainer && document.body) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.className = 'position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '1080';
            document.body.appendChild(toastContainer);
        } else if (!document.body) {
            console.error('Document body not available');
            return;
        }

        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast ${type} border-0`;
        toast.setAttribute('role', 'alert');
        
        // Create toast content
        const toastHeader = document.createElement('div');
        toastHeader.className = 'toast-header bg-' + type + ' text-white';
        toastHeader.innerHTML = `
            <strong class="me-auto">${type.charAt(0).toUpperCase() + type.slice(1)}</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
        `;
        
        const toastBody = document.createElement('div');
        toastBody.className = 'toast-body';
        toastBody.textContent = message;
        
        toast.appendChild(toastHeader);
        toast.appendChild(toastBody);
        
        // Add toast to container
        toastContainer.appendChild(toast);

        // Initialize and show toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        // Remove toast after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    } catch (error) {
        console.error('Error showing toast:', error);
    }
}

function openStockModal(itemId, itemName, currentStock) {
    // Initialize modal elements if they don't exist
    const stockItemId = document.getElementById('stockItemId') || document.createElement('input');
    const itemNameInput = document.getElementById('itemName') || document.createElement('input');
    const currentStockInput = document.getElementById('currentStock') || document.createElement('input');
    const newStockInput = document.getElementById('newStock') || document.createElement('input');
    const modalElement = document.getElementById('stockModal') || document.createElement('div');

    // Set values if elements exist
    if (stockItemId) stockItemId.value = itemId;
    if (itemNameInput) itemNameInput.value = itemName;
    if (currentStockInput) currentStockInput.value = currentStock;
    if (newStockInput) {
        newStockInput.value = currentStock;
        newStockInput.focus();
    }
    
    // Initialize and show modal if it exists
    if (modalElement) {
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
    }
}

function updateStock() {
    const itemId = document.getElementById('stockItemId').value;
    const newStock = document.getElementById('newStock').value;
    
    if (!newStock || isNaN(newStock)) {
        showToast('error', 'Please enter a valid number for stock');
        return;
    }

    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    if (!csrfToken) {
        showToast('error', 'CSRF token not found. Please reload the page.');
        return;
    }

    fetch(`/update_stock`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken
        },
        body: JSON.stringify({
            item_id: itemId,
            new_stock: parseInt(newStock)
        })
    })
    .then(async response => {
    let data;
    try {
        data = await response.json();
    } catch (e) {
        // Not JSON, try text
        const text = await response.text();
        throw new Error(text || 'Request failed');
    }
    if (!response.ok) {
        throw new Error(data.error || data.message || 'Failed to update stock');
    }
    return data;
})
    .then(data => {
        if (data.success) {
            // Update the stock display
            const stockElement = document.getElementById(`stock-${itemId}`);
            if (stockElement) {
                stockElement.textContent = newStock;
            }
            
            // Close the modal and clean up overlay
            const modalElement = document.getElementById('stockModal');
            if (modalElement) {
                // Remove any existing modal instance
                const modal = bootstrap.Modal.getInstance(modalElement);
                if (modal) {
                    modal.hide();
                }
                
                // Create new modal instance and hide it
                const newModal = new bootstrap.Modal(modalElement);
                newModal.hide();
                
                // Remove the backdrop manually if it exists
                const backdrop = document.querySelector('.modal-backdrop');
                if (backdrop) {
                    backdrop.remove();
                }
            }
            
            // Show success message
            showToast('success', 'Stock updated successfully');
            
            // Force a reflow to ensure modal cleanup
            modalElement.style.display = 'none';
            modalElement.offsetHeight; // Trigger reflow
            modalElement.style.display = '';
        } else {
            throw new Error(data.error || 'Failed to update stock');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('error', error.message || 'Failed to update stock');
    });
}

// Stock management initialization is now handled in initializeDashboard function    
// Initialize dashboard updates
// initializeDashboardUpdates(); // This function is now handled by Socket.IO