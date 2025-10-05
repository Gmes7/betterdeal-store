// Main JavaScript functionality for BetterDeal e-commerce

class BetterDealApp {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.updateCartBadge();
    }

    setupEventListeners() {
        // Search functionality
        this.setupSearch();

        // Cart functionality
        this.setupCart();

        // Product interactions
        this.setupProductInteractions();
    }

    setupSearch() {
        const searchInput = document.querySelector('.search-input');
        if (searchInput) {
            // Real-time search suggestions could be added here
            searchInput.addEventListener('input', this.debounce((e) => {
                // Future: Add real-time search suggestions
            }, 300));
        }
    }

    setupCart() {
        // Cart quantity updates
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('cart-quantity-btn')) {
                this.handleQuantityUpdate(e);
            }
        });
    }

    setupProductInteractions() {
        // Product card interactions
        document.addEventListener('click', (e) => {
            if (e.target.closest('.product-card')) {
                const productCard = e.target.closest('.product-card');
                const productId = productCard.dataset.productId;
                if (productId) {
                    window.location.href = `/product/${productId}`;
                }
            }
        });
    }

    async addToCart(productId, quantity = 1) {
        try {
            const formData = new FormData();
            formData.append('product_id', productId);
            formData.append('quantity', quantity);

            const response = await fetch('/add_to_cart', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification('Product added to cart!', 'success');
                this.updateCartBadge(data.cart_count);
                return true;
            } else {
                this.showNotification('Failed to add product to cart', 'error');
                return false;
            }
        } catch (error) {
            console.error('Error adding to cart:', error);
            this.showNotification('Error adding product to cart', 'error');
            return false;
        }
    }

    async updateCartQuantity(productId, quantity) {
        try {
            const formData = new FormData();
            formData.append('product_id', productId);
            formData.append('quantity', quantity);

            const response = await fetch('/update_cart', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                this.updateCartBadge(data.cart_count);
                // Reload to update prices
                setTimeout(() => location.reload(), 300);
                return true;
            } else {
                this.showNotification('Failed to update cart', 'error');
                return false;
            }
        } catch (error) {
            console.error('Error updating cart:', error);
            this.showNotification('Error updating cart', 'error');
            return false;
        }
    }

    async removeFromCart(productId) {
        if (!confirm('Are you sure you want to remove this item from your cart?')) {
            return false;
        }

        try {
            const formData = new FormData();
            formData.append('product_id', productId);

            const response = await fetch('/remove_from_cart', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification('Item removed from cart', 'success');
                this.updateCartBadge(data.cart_count);
                // Remove item from DOM or reload
                setTimeout(() => location.reload(), 300);
                return true;
            } else {
                this.showNotification('Failed to remove item from cart', 'error');
                return false;
            }
        } catch (error) {
            console.error('Error removing from cart:', error);
            this.showNotification('Error removing item from cart', 'error');
            return false;
        }
    }

    async clearCart() {
        if (!confirm('Are you sure you want to clear your entire cart?')) {
            return false;
        }

        try {
            const response = await fetch('/clear_cart', {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification('Cart cleared', 'success');
                this.updateCartBadge(0);
                setTimeout(() => location.reload(), 300);
                return true;
            } else {
                this.showNotification('Failed to clear cart', 'error');
                return false;
            }
        } catch (error) {
            console.error('Error clearing cart:', error);
            this.showNotification('Error clearing cart', 'error');
            return false;
        }
    }

    updateCartBadge(count) {
        const cartBadge = document.querySelector('.cart-badge');
        if (cartBadge) {
            if (count > 0) {
                cartBadge.textContent = count;
                cartBadge.style.display = 'flex';
                cartBadge.classList.add('update');
                setTimeout(() => cartBadge.classList.remove('update'), 600);
            } else {
                cartBadge.style.display = 'none';
            }
        }
    }

    showNotification(message, type = 'info') {
        // Remove existing notifications
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(notification => notification.remove());

        const notification = document.createElement('div');
        notification.className = `notification ${type}-message`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: 4px;
            color: white;
            font-weight: bold;
            z-index: 10000;
            animation: slideIn 0.3s ease;
            max-width: 300px;
        `;

        if (type === 'success') {
            notification.style.background = 'var(--success)';
        } else if (type === 'error') {
            notification.style.background = 'var(--danger)';
        } else {
            notification.style.background = 'var(--primary-blue)';
        }

        notification.textContent = message;
        document.body.appendChild(notification);

        // Auto remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    handleQuantityUpdate(e) {
        const button = e.target;
        const container = button.closest('.quantity-controls');
        const quantityDisplay = container.querySelector('.quantity-display');
        let quantity = parseInt(quantityDisplay.textContent);

        if (button.classList.contains('decrease')) {
            quantity = Math.max(1, quantity - 1);
        } else if (button.classList.contains('increase')) {
            quantity = quantity + 1;
        }

        quantityDisplay.textContent = quantity;

        // If we're on a product page, update the total price
        this.updateProductTotal(quantity);
    }

    updateProductTotal(quantity) {
        const priceElement = document.querySelector('.current-price');
        if (priceElement) {
            const price = parseFloat(priceElement.textContent.replace('$', ''));
            const total = price * quantity;

            const totalElement = document.getElementById('total-price');
            if (totalElement) {
                totalElement.textContent = `$${total.toFixed(2)}`;
            }
        }
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.betterDealApp = new BetterDealApp();
});

// Utility functions for product pages
function updateQuantity(change) {
    const quantityElement = document.getElementById('quantity');
    let quantity = parseInt(quantityElement.textContent);
    const maxStock = parseInt(quantityElement.dataset.maxStock || 999);

    quantity += change;
    quantity = Math.max(1, Math.min(maxStock, quantity));
    quantityElement.textContent = quantity;

    // Update total price
    updateTotalPrice(quantity);
}

function updateTotalPrice(quantity) {
    const priceElement = document.querySelector('.current-price');
    if (priceElement) {
        const price = parseFloat(priceElement.textContent.replace('$', ''));
        const total = price * quantity;

        let totalElement = document.getElementById('total-price');
        if (!totalElement) {
            totalElement = document.createElement('div');
            totalElement.id = 'total-price';
            totalElement.className = 'total-price';
            totalElement.style.cssText = 'font-size: 1.2rem; font-weight: bold; margin: 1rem 0; color: var(--primary-blue);';
            priceElement.parentNode.appendChild(totalElement);
        }

        totalElement.textContent = `Total: $${total.toFixed(2)}`;
    }
}

// Add CSS for notifications
const notificationStyles = `
@keyframes slideIn {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

@keyframes slideOut {
    from { transform: translateX(0); opacity: 1; }
    to { transform: translateX(100%); opacity: 0; }
}

.notification {
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
`;

const styleSheet = document.createElement('style');
styleSheet.textContent = notificationStyles;
document.head.appendChild(styleSheet);

// Add these functions to your main.js or include them in cart.html

function updateCartTotals() {
    let subtotal = 0;

    // Calculate new subtotal from all items
    const cartItems = document.querySelectorAll('[id^="cart-item-"]');
    cartItems.forEach(item => {
        const productId = item.id.replace('cart-item-', '');
        const quantity = parseInt(document.getElementById(`quantity-${productId}`).textContent);
        const price = parseFloat(document.getElementById(`item-total-${productId}`).textContent) / quantity;
        const itemTotal = price * quantity;

        // Update individual item total
        document.getElementById(`item-total-${productId}`).textContent = itemTotal.toFixed(2);
        subtotal += itemTotal;
    });

    // Calculate shipping
    const shipping = subtotal >= 35 ? 0 : 4.99;
    const total = subtotal + shipping;

    // Update display
    document.getElementById('subtotal-display').textContent = subtotal.toFixed(2);
    document.getElementById('total-display').textContent = total.toFixed(2);

    // Update shipping display
    const shippingDisplay = document.getElementById('shipping-display');
    if (shipping === 0) {
        shippingDisplay.innerHTML = '<span class="text-success">FREE</span>';
    } else {
        shippingDisplay.textContent = '$' + shipping.toFixed(2);
    }

    // Update shipping message
    const shippingMessage = document.getElementById('shipping-message');
    const shippingDifference = document.getElementById('shipping-difference');
    if (subtotal < 35) {
        shippingMessage.style.display = 'block';
        shippingDifference.textContent = (35 - subtotal).toFixed(2);
    } else {
        shippingMessage.style.display = 'none';
    }
}

function highlightUpdatedItem(productId) {
    const itemElement = document.getElementById(`cart-item-${productId}`);
    if (itemElement) {
        itemElement.classList.add('cart-update');
        setTimeout(() => {
            itemElement.classList.remove('cart-update');
        }, 1000);
    }
}