from flask import Flask, render_template, request, session, redirect, url_for, jsonify, make_response
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import csv
import smtplib
import json
import threading
import os
from flask import Flask, session
from flask_session import Session  # Add this import



app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')

# Session configuration for production
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = '/tmp/flask_session'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_COOKIE_SECURE'] = True  # For HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize session
Session(app)
# Admin credentials (change these in production)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # Change this in production

# File to store products and orders
PRODUCTS_FILE = "products.json"
ORDERS_FILE = "orders.json"
ADMIN_EMAIL = "admin@betterdeal.com"  # Change to your email

EMPLOYEES_FILE = "employees.json"
EXPENSES_FILE = "expenses.json"

def load_products():
    """Load products from JSON file"""
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_products(products):
    """Save products to JSON file"""
    with open(PRODUCTS_FILE, 'w') as f:
        json.dump(products, f, indent=2)

def load_orders():
    """Load orders from JSON file"""
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_orders(orders):
    """Save orders to JSON file"""
    with open(ORDERS_FILE, 'w') as f:
        json.dump(orders, f, indent=2)

def get_next_product_id():
    """Get next available product ID"""
    products = load_products()
    if not products:
        return 1
    return max(product['id'] for product in products) + 1

def get_next_order_id():
    """Get next available order ID"""
    orders = load_orders()
    if not orders:
        return 1001
    return max(order['id'] for order in orders) + 1

def get_categories():
    """Get all unique categories from products"""
    products = load_products()
    categories = set(product['category'] for product in products)
    category_icons = {
        'Electronics': '📱',
        'Clothing': '👕',
        'Home & Garden': '🏠',
        'Sports': '⚽',
        'Beauty': '💄',
        'Grocery': '🛒'
    }
    return [{"name": category, "icon": category_icons.get(category, '📦'),
             "count": len([p for p in products if p['category'] == category])} for category in categories]


def send_order_notification(order):
    """Send email notification to both customer and admin"""
    try:
        # Email configuration - UPDATE THESE
        SMTP_SERVER = "smtp.gmail.com"
        SMTP_PORT = 587
        EMAIL_USERNAME = "your-email@gmail.com"  # Your store email
        EMAIL_PASSWORD = "your-app-password"  # Your app password

        # Determine who to send notifications to
        recipients = []

        # Always send to admin/store email
        recipients.append(EMAIL_USERNAME)

        # Send to customer if they provided an email
        if order.get('customer_email'):
            recipients.append(order['customer_email'])

        # You can also add additional admin emails
        additional_admins = ["manager@betterdeal.com", "owner@betterdeal.com"]  # Add more if needed
        recipients.extend(additional_admins)

        # Remove duplicates
        recipients = list(set(recipients))

        # Create customer-facing email
        customer_msg = MIMEMultipart('alternative')
        customer_msg['From'] = f"BetterDeal Store <{EMAIL_USERNAME}>"
        customer_msg['To'] = order.get('customer_email', '')  # Only to customer
        customer_msg['Subject'] = f"✅ Order Confirmation #${order['id']} - BetterDeal"

        # Customer email content
        customer_text = f"""
        Thank you for your order!

        ORDER CONFIRMATION
        Order ID: #{order['id']}
        Order Date: {order['order_date']}

        Order Summary:
        Subtotal: ${order['subtotal']:.2f}
        Shipping: ${order['shipping']:.2f}
        Total: ${order['total_amount']:.2f}

        Items Ordered:
        """
        for item in order['items']:
            customer_text += f"- {item['name']} x {item['quantity']} = ${item['total']:.2f}\n"

        customer_text += f"""
        Delivery Address:
        {order['delivery_address']}

        Payment Method: {order['payment_method']}
        Status: {order['status'].title()}

        We'll notify you when your order ships!
        Thank you for shopping with BetterDeal!
        """

        customer_html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd;">
              <h2 style="color: #0071CE;">✅ Order Confirmation</h2>
              <p>Thank you for your order! We're getting it ready for you.</p>

              <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="margin-top: 0;">Order Details</h3>
                <p><strong>Order ID:</strong> #{order['id']}</p>
                <p><strong>Order Date:</strong> {order['order_date']}</p>
                <p><strong>Status:</strong> <span style="color: #28a745;">{order['status'].title()}</span></p>
              </div>

              <div style="margin: 20px 0;">
                <h3>Order Summary</h3>
                <table style="width: 100%; border-collapse: collapse;">
                  <tr>
                    <td style="padding: 5px;">Subtotal:</td>
                    <td style="text-align: right; padding: 5px;">${order['subtotal']:.2f}</td>
                  </tr>
                  <tr>
                    <td style="padding: 5px;">Shipping:</td>
                    <td style="text-align: right; padding: 5px;">${order['shipping']:.2f}</td>
                  </tr>
                  <tr style="font-weight: bold; border-top: 2px solid #0071CE;">
                    <td style="padding: 5px;">Total:</td>
                    <td style="text-align: right; padding: 5px;">${order['total_amount']:.2f}</td>
                  </tr>
                </table>
              </div>

              <div style="margin: 20px 0;">
                <h3>Items Ordered</h3>
                <ul style="list-style: none; padding: 0;">
        """
        for item in order['items']:
            customer_html += f"""
                  <li style="padding: 10px; border-bottom: 1px solid #eee;">
                    {item['name']} x {item['quantity']} = <strong>${item['total']:.2f}</strong>
                  </li>
            """

        customer_html += f"""
                </ul>
              </div>

              <div style="background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h4 style="margin-top: 0;">Delivery Information</h4>
                <p><strong>Address:</strong><br>{order['delivery_address'].replace(chr(10), '<br>')}</p>
                <p><strong>Payment Method:</strong> {order['payment_method'].upper()}</p>
              </div>

              <p>We'll notify you when your order ships!</p>
              <p>Thank you for shopping with <strong>BetterDeal</strong>!</p>
            </div>
          </body>
        </html>
        """

        # Attach both versions for customer
        part1 = MIMEText(customer_text, 'plain')
        part2 = MIMEText(customer_html, 'html')
        customer_msg.attach(part1)
        customer_msg.attach(part2)

        # Create admin notification email
        admin_msg = MIMEMultipart('alternative')
        admin_msg['From'] = f"BetterDeal Store <{EMAIL_USERNAME}>"
        admin_msg['To'] = EMAIL_USERNAME
        admin_msg['Subject'] = f"🛍️ New Order #{order['id']} - ${order['total_amount']:.2f}"

        # Admin email content
        admin_text = f"""
        NEW ORDER RECEIVED!

        Order ID: #{order['id']}
        Order Date: {order['order_date']}

        Customer Information:
        Name: {order['customer_name']}
        Email: {order.get('customer_email', 'Not provided')}
        Phone: {order.get('customer_phone', 'Not provided')}

        Order Total: ${order['total_amount']:.2f}
        Payment Method: {order['payment_method']}

        Order Items:
        """
        for item in order['items']:
            admin_text += f"- {item['name']} x {item['quantity']} = ${item['total']:.2f}\n"

        admin_text += f"""
        Delivery Address:
        {order['delivery_address']}

        Order breakdown:
        Subtotal: ${order['subtotal']:.2f}
        Shipping: ${order['shipping']:.2f}
        Total: ${order['total_amount']:.2f}
        """

        admin_html = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #0071CE;">🛍️ New Order Received!</h2>

            <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0;">
              <h3 style="margin-top: 0;">Order #{order['id']} - ${order['total_amount']:.2f}</h3>
              <p><strong>Date:</strong> {order['order_date']}</p>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">
              <div>
                <h4>Customer Information</h4>
                <p><strong>Name:</strong> {order['customer_name']}</p>
                <p><strong>Email:</strong> {order.get('customer_email', 'Not provided')}</p>
                <p><strong>Phone:</strong> {order.get('customer_phone', 'Not provided')}</p>
                <p><strong>Payment:</strong> {order['payment_method'].upper()}</p>
              </div>

              <div>
                <h4>Order Summary</h4>
                <p>Subtotal: ${order['subtotal']:.2f}</p>
                <p>Shipping: ${order['shipping']:.2f}</p>
                <p><strong>Total: ${order['total_amount']:.2f}</strong></p>
              </div>
            </div>

            <h4>Order Items</h4>
            <table style="width: 100%; border-collapse: collapse;">
              <thead>
                <tr style="background: #0071CE; color: white;">
                  <th style="padding: 10px; text-align: left;">Item</th>
                  <th style="padding: 10px; text-align: center;">Qty</th>
                  <th style="padding: 10px; text-align: right;">Total</th>
                </tr>
              </thead>
              <tbody>
        """
        for item in order['items']:
            admin_html += f"""
                <tr>
                  <td style="padding: 10px; border-bottom: 1px solid #ddd;">{item['name']}</td>
                  <td style="padding: 10px; text-align: center; border-bottom: 1px solid #ddd;">{item['quantity']}</td>
                  <td style="padding: 10px; text-align: right; border-bottom: 1px solid #ddd;">${item['total']:.2f}</td>
                </tr>
            """

        admin_html += f"""
              </tbody>
            </table>

            <div style="margin-top: 20px; padding: 15px; background: #e9ecef; border-radius: 5px;">
              <h4>Delivery Address</h4>
              <p>{order['delivery_address'].replace(chr(10), '<br>')}</p>
            </div>
          </body>
        </html>
        """

        # Attach both versions for admin
        part3 = MIMEText(admin_text, 'plain')
        part4 = MIMEText(admin_html, 'html')
        admin_msg.attach(part3)
        admin_msg.attach(part4)

        # Send emails
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)

        # Send customer confirmation (if email provided)
        if order.get('customer_email'):
            server.send_message(customer_msg)
            print(f"📧 Customer confirmation sent to: {order['customer_email']}")

        # Send admin notification
        server.send_message(admin_msg)
        print(f"📧 Admin notification sent for order #{order['id']}")

        server.quit()

        print(f"✅ All notifications sent for order #{order['id']}")
        return True

    except Exception as e:
        print(f"❌ Error sending email notifications: {e}")
        return False


def send_sms_notification(order):
    """Send SMS notification if phone number is provided"""
    try:
        # This is a basic template. You'll need to integrate with an SMS service like:
        # Twilio, Nexmo, or your local SMS gateway

        if not order.get('customer_phone'):
            return False

        phone_number = order['customer_phone']
        message = f"BetterDeal: Order #{order['id']} confirmed! Total: ${order['total_amount']:.2f}. We'll notify you when it ships."

        # Example with Twilio (you need to install twilio: pip install twilio)
        # from twilio.rest import Client

        # account_sid = 'your_account_sid'
        # auth_token = 'your_auth_token'
        # client = Client(account_sid, auth_token)

        # message = client.messages.create(
        #     body=message,
        #     from_='+1234567890',  # Your Twilio number
        #     to=phone_number
        # )

        print(f"📱 SMS notification would be sent to: {phone_number}")
        print(f"💬 Message: {message}")
        return True

    except Exception as e:
        print(f"❌ Error sending SMS: {e}")
        return False

# Initialize sample products if file doesn't exist
def initialize_products():
    if not os.path.exists(PRODUCTS_FILE):
        sample_products = [
            {
                "id": 1,
                "name": "Samsung Galaxy S24",
                "brand": "Samsung",
                "price": 799.99,
                "original_price": 899.99,
                "discount": 11,
                "category": "Electronics",
                "image": "https://via.placeholder.com/400x400/0071CE/FFFFFF?text=Samsung+Galaxy",
                "rating": 4.5,
                "reviews": 128,
                "stock": 15,
                "description": "Latest Samsung smartphone with advanced camera and AI features",
                "featured": True,
                "active": True
            },
            {
                "id": 2,
                "name": "Nike Air Max 270",
                "brand": "Nike",
                "price": 129.99,
                "original_price": 149.99,
                "discount": 13,
                "category": "Clothing",
                "image": "https://via.placeholder.com/400x400/0071CE/FFFFFF?text=Nike+Shoes",
                "rating": 4.3,
                "reviews": 89,
                "stock": 25,
                "description": "Comfortable running shoes with Air Max technology",
                "featured": True,
                "active": True
            },
            {
                "id": 3,
                "name": "KitchenAid Mixer",
                "brand": "KitchenAid",
                "price": 299.99,
                "original_price": 349.99,
                "discount": 14,
                "category": "Home & Garden",
                "image": "https://via.placeholder.com/400x400/0071CE/FFFFFF?text=Mixer",
                "rating": 4.7,
                "reviews": 203,
                "stock": 8,
                "description": "Professional stand mixer for all your baking needs",
                "featured": True,
                "active": True
            },
            {
                "id": 4,
                "name": "Yoga Mat Premium",
                "brand": "Gaiam",
                "price": 39.99,
                "original_price": 49.99,
                "discount": 20,
                "category": "Sports",
                "image": "https://via.placeholder.com/400x400/0071CE/FFFFFF?text=Yoga+Mat",
                "rating": 4.2,
                "reviews": 156,
                "stock": 30,
                "description": "Non-slip yoga mat for comfortable workouts",
                "featured": False,
                "active": True
            }
        ]
        save_products(sample_products)

# Initialize products on startup
initialize_products()

def load_employees():
    """Load employees from JSON file"""
    if os.path.exists(EMPLOYEES_FILE):
        with open(EMPLOYEES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_employees(employees):
    """Save employees to JSON file"""
    with open(EMPLOYEES_FILE, 'w') as f:
        json.dump(employees, f, indent=2)

def load_expenses():
    """Load expenses from JSON file"""
    if os.path.exists(EXPENSES_FILE):
        with open(EXPENSES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_expenses(expenses):
    """Save expenses to JSON file"""
    with open(EXPENSES_FILE, 'w') as f:
        json.dump(expenses, f, indent=2)

def initialize_sample_data():
    """Initialize sample business data"""
    # Sample employees
    if not os.path.exists(EMPLOYEES_FILE):
        sample_employees = [
            {
                "id": 1,
                "name": "John Smith",
                "position": "Manager",
                "salary": 3000,
                "email": "john@betterdeal.com",
                "phone": "+1234567890",
                "hire_date": "2024-01-15",
                "status": "active"
            },
            {
                "id": 2,
                "name": "Maria Garcia",
                "position": "Sales Associate",
                "salary": 2000,
                "email": "maria@betterdeal.com",
                "phone": "+1234567891",
                "hire_date": "2024-02-01",
                "status": "active"
            }
        ]
        save_employees(sample_employees)

    # Sample expenses
    if not os.path.exists(EXPENSES_FILE):
        sample_expenses = [
            {
                "id": 1,
                "date": "2024-03-01",
                "category": "Rent",
                "description": "Store Rent",
                "amount": 1500,
                "payment_method": "bank_transfer"
            },
            {
                "id": 2,
                "date": "2024-03-02",
                "category": "Utilities",
                "description": "Electricity Bill",
                "amount": 300,
                "payment_method": "bank_transfer"
            }
        ]
        save_expenses(sample_expenses)

# Initialize sample data
initialize_sample_data()

def get_financial_reports():
    """Generate financial reports"""
    orders = load_orders()
    expenses = load_expenses()
    employees = load_employees()

    # Calculate time periods
    today = datetime.now()
    current_month = today.strftime("%Y-%m")
    last_month = (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

    # Current month calculations
    current_month_orders = [o for o in orders if o['order_date'].startswith(current_month)]
    current_month_expenses = [e for e in expenses if e['date'].startswith(current_month)]

    # Last month calculations
    last_month_orders = [o for o in orders if o['order_date'].startswith(last_month)]
    last_month_expenses = [e for e in expenses if e['date'].startswith(last_month)]

    # Revenue calculations
    current_month_revenue = sum(order['total_amount'] for order in current_month_orders)
    last_month_revenue = sum(order['total_amount'] for order in last_month_orders)

    # Expense calculations
    current_month_expense_total = sum(expense['amount'] for expense in current_month_expenses)
    last_month_expense_total = sum(expense['amount'] for expense in last_month_expenses)

    # Employee costs
    current_month_salaries = sum(emp['salary'] for emp in employees if emp['status'] == 'active')

    # Profit calculations
    current_month_profit = current_month_revenue - current_month_expense_total - current_month_salaries
    last_month_profit = last_month_revenue - last_month_expense_total - current_month_salaries

    # Growth calculations
    revenue_growth = ((current_month_revenue - last_month_revenue) / last_month_revenue * 100) if last_month_revenue > 0 else 0
    profit_growth = ((current_month_profit - last_month_profit) / abs(last_month_profit) * 100) if last_month_profit != 0 else 0

    return {
        'current_month': current_month,
        'last_month': last_month,
        'revenue': {
            'current': current_month_revenue,
            'last': last_month_revenue,
            'growth': revenue_growth
        },
        'expenses': {
            'current': current_month_expense_total,
            'last': last_month_expense_total,
            'growth': ((current_month_expense_total - last_month_expense_total) / last_month_expense_total * 100) if last_month_expense_total > 0 else 0
        },
        'profit': {
            'current': current_month_profit,
            'last': last_month_profit,
            'growth': profit_growth
        },
        'salaries': current_month_salaries,
        'order_count': len(current_month_orders),
        'average_order_value': current_month_revenue / len(current_month_orders) if current_month_orders else 0
    }

def get_cart_count():
    """Get total number of items in cart"""
    cart = session.get('cart', {})
    total = 0
    for item in cart.values():
        if isinstance(item, dict):
            # New format: {'quantity': X}
            total += item.get('quantity', 0)
        else:
            # Old format: just the quantity number
            total += item
    return total

@app.context_processor
def inject_cart_count():
    return dict(cart_count=get_cart_count())

@app.context_processor
def inject_now():
    return {'today': datetime.now()}

# Main Store Routes
@app.route('/')
def index():
    products = load_products()
    featured_products = [p for p in products if p.get('featured') and p.get('active', True)][:4]
    best_sellers = [p for p in products if p.get('active', True)][:8]
    categories = get_categories()
    return render_template('index.html',
                           featured_products=featured_products,
                           best_sellers=best_sellers,
                           categories=categories)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    products = load_products()
    product = next((p for p in products if p['id'] == product_id and p.get('active', True)), None)
    if not product:
        return "Product not found", 404
    return render_template('product.html', product=product)


@app.route('/cart')
def cart():
    cart_items = []
    subtotal = 0
    cart_data = session.get('cart', {})

    products = load_products()
    for product_id, item_data in cart_data.items():
        product = next((p for p in products if p['id'] == int(product_id)), None)
        if product:
            # Handle both data formats
            if isinstance(item_data, dict):
                quantity = item_data.get('quantity', 1)
            else:
                quantity = item_data  # Old format

            item_total = product['price'] * quantity
            cart_items.append({
                'id': product['id'],
                'name': product['name'],
                'brand': product['brand'],
                'price': product['price'],
                'image': product['image'],
                'rating': product.get('rating', 4.5),
                'quantity': quantity,
                'item_total': item_total
            })
            subtotal += item_total

    shipping = 0 if subtotal >= 35 else 4.99
    final_total = subtotal + shipping

    return render_template('cart.html',
                           cart_items=cart_items,
                           subtotal=subtotal,
                           shipping=shipping,
                           final_total=final_total)


@app.route('/checkout')
def checkout():
    cart_data = session.get('cart', {})
    if not cart_data:
        return redirect(url_for('cart'))

    cart_items = []
    subtotal = 0
    products = load_products()
    for product_id, item_data in cart_data.items():
        product = next((p for p in products if p['id'] == int(product_id)), None)
        if product:
            # Handle both data formats
            if isinstance(item_data, dict):
                quantity = item_data.get('quantity', 1)
            else:
                quantity = item_data  # Old format

            item_total = product['price'] * quantity
            cart_items.append({
                'id': product['id'],
                'name': product['name'],
                'brand': product['brand'],
                'price': product['price'],
                'image': product['image'],
                'quantity': quantity,
                'item_total': item_total
            })
            subtotal += item_total

    shipping = 0 if subtotal >= 35 else 4.99
    final_total = subtotal + shipping

    return render_template('checkout.html',
                           cart_items=cart_items,
                           subtotal=subtotal,
                           shipping=shipping,
                           final_total=final_total)


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    try:
        product_id = request.form.get('product_id')
        quantity = int(request.form.get('quantity', 1))

        print(f"🛒 ADD_TO_CART - Product ID: {product_id}, Quantity: {quantity}")

        # Vérifier que le produit existe
        products = load_products()
        product = next((p for p in products if p['id'] == int(product_id)), None)
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'})

        # Initialiser le panier si nécessaire
        if 'cart' not in session:
            session['cart'] = {}
            print("🛒 New cart created")

        cart = session['cart']
        product_id_str = str(product_id)

        # Ajouter ou mettre à jour le produit
        if product_id_str in cart:
            if isinstance(cart[product_id_str], dict):
                cart[product_id_str]['quantity'] += quantity
            else:
                # Convertir l'ancien format
                cart[product_id_str] = {'quantity': cart[product_id_str] + quantity}
            print(f"🛒 Updated product {product_id} to quantity {cart[product_id_str]['quantity']}")
        else:
            cart[product_id_str] = {'quantity': quantity}
            print(f"🛒 Added new product {product_id} with quantity {quantity}")

        # Sauvegarder la session
        session['cart'] = cart
        session.modified = True

        # Forcer la sauvegarde
        if hasattr(session, 'save'):
            session.save()

        cart_count = get_cart_count()
        print(f"🛒 Final cart count: {cart_count}")
        print(f"🛒 Cart contents: {cart}")

        return jsonify({
            'success': True,
            'cart_count': cart_count,
            'message': f'{product["name"]} added to cart!'
        })

    except Exception as e:
        print(f"❌ ERROR in add_to_cart: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/reset_cart')
def reset_cart():
    """Temporary route to reset cart format"""
    session.pop('cart', None)
    return "Cart reset successfully. <a href='/'>Go Home</a>"


@app.route('/update_cart_quantity', methods=['POST'])
def update_cart_quantity():
    """Update cart quantity with + and - buttons"""
    try:
        product_id = request.form.get('product_id')
        action = request.form.get('action')

        print(f"Updating cart: product_id={product_id}, action={action}")  # Debug log

        if 'cart' not in session:
            session['cart'] = {}
            print("Cart initialized")  # Debug log

        cart = session['cart']

        if product_id in cart:
            if action == 'increase':
                cart[product_id]['quantity'] += 1
                print(f"Increased quantity to: {cart[product_id]['quantity']}")  # Debug log
            elif action == 'decrease':
                if cart[product_id]['quantity'] > 1:
                    cart[product_id]['quantity'] -= 1
                    print(f"Decreased quantity to: {cart[product_id]['quantity']}")  # Debug log
                else:
                    # Remove item if quantity becomes 0
                    cart.pop(product_id, None)
                    print("Item removed from cart")  # Debug log
        else:
            print(f"Product {product_id} not found in cart")  # Debug log
            return jsonify({'success': False, 'message': 'Product not in cart'})

        # Calculate the updated item total
        products = load_products()
        product = next((p for p in products if p['id'] == int(product_id)), None)
        item_total = 0
        if product and product_id in cart:
            item_total = product['price'] * cart[product_id]['quantity']

        # Ensure session is saved
        session['cart'] = cart
        session.modified = True

        # Force session save
        if hasattr(session, 'save'):
            session.save()

        print(f"Session saved: {session.get('cart')}")  # Debug log

        return jsonify({
            'success': True,
            'cart_count': get_cart_count(),
            'item_total': round(item_total, 2),
            'cart': cart
        })
    except Exception as e:
        print(f"Error in update_cart_quantity: {str(e)}")  # Debug log
        return jsonify({'success': False, 'message': str(e)})


@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    """Remove item from cart"""
    try:
        product_id = request.form.get('product_id')

        cart = session.get('cart', {})
        if product_id in cart:
            cart.pop(product_id, None)

        session['cart'] = cart
        session.modified = True

        return jsonify({'success': True, 'cart_count': get_cart_count()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/clear_cart', methods=['POST'])
def clear_cart():
    """Clear entire cart"""
    try:
        session.pop('cart', None)
        return jsonify({'success': True, 'cart_count': 0})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/search')
def search():
    query = request.args.get('q', '').lower()
    results = []

    products = load_products()
    if query:
        for product in products:
            if (query in product['name'].lower() or
                    query in product['brand'].lower() or
                    query in product['category'].lower() or
                    query in product['description'].lower()):
                results.append(product)

    return render_template('search.html', query=query, results=results, results_count=len(results))

@app.route('/place_order', methods=['POST'])
def place_order():
    """Handle order placement"""
    try:
        cart_data = session.get('cart', {})
        if not cart_data:
            return jsonify({'success': False, 'message': 'Cart is empty'})

        # Get customer information
        customer_name = request.form.get('customer_name')
        customer_email = request.form.get('customer_email')
        customer_phone = request.form.get('customer_phone')
        delivery_address = request.form.get('delivery_address')
        payment_method = request.form.get('payment_method')

        # Calculate order total
        products = load_products()
        cart_items = []
        total_amount = 0

        for product_id, item in cart_data.items():
            product = next((p for p in products if p['id'] == int(product_id)), None)
            if product:
                item_total = product['price'] * item['quantity']
                cart_items.append({
                    'product_id': product['id'],
                    'name': product['name'],
                    'price': product['price'],
                    'quantity': item['quantity'],
                    'total': item_total
                })
                total_amount += item_total

        shipping = 0 if total_amount >= 35 else 4.99
        total_amount += shipping

        # Create order
        order = {
            'id': get_next_order_id(),
            'customer_name': customer_name,
            'customer_email': customer_email,
            'customer_phone': customer_phone,
            'delivery_address': delivery_address,
            'payment_method': payment_method,
            'items': cart_items,
            'subtotal': total_amount - shipping,
            'shipping': shipping,
            'total_amount': total_amount,
            'status': 'pending',  # pending, confirmed, shipped, delivered, cancelled
            'order_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'delivery_date': None
        }

        # Save order
        orders = load_orders()
        orders.append(order)
        save_orders(orders)

        # Clear cart
        session.pop('cart', None)

        # Send notifications (in background)
        threading.Thread(target=send_order_notification, args=(order,)).start()
        threading.Thread(target=send_sms_notification, args=(order,)).start()  # Optional SMS
        return jsonify({
            'success': True,
            'order_id': order['id'],
            'message': f'Order placed successfully! Order ID: {order["id"]}'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error placing order: {str(e)}'})

@app.route('/process_payment', methods=['POST'])
def process_payment():
    payment_method = request.form.get('payment_method')

    if payment_method in ['moncash', 'natcash']:
        # Simulate payment processing
        session.pop('cart', None)
        return jsonify({
            'success': True,
            'message': f'Payment processed successfully with {payment_method.upper()}',
            'order_id': f'ORDER-{datetime.now().strftime("%Y%m%d%H%M%S")}'
        })
    elif payment_method == 'cod':
        # Cash on delivery
        session.pop('cart', None)
        return jsonify({
            'success': True,
            'message': 'Order placed successfully! Pay when you receive your items.',
            'order_id': f'ORDER-{datetime.now().strftime("%Y%m%d%H%M%S")}'
        })
    else:
        return jsonify({'success': False, 'message': 'Invalid payment method'})

# Admin Routes
@app.route('/admin')
def admin_login_page():
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    username = request.form.get('username')
    password = request.form.get('password')

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['admin_logged_in'] = True
        return redirect(url_for('admin_dashboard'))
    else:
        return "Invalid credentials", 401

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login_page'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login_page'))

    products = load_products()
    orders = load_orders()

    total_products = len(products)
    active_products = len([p for p in products if p.get('active', True)])
    low_stock_products = len([p for p in products if p.get('stock', 0) < 10 and p.get('active', True)])
    out_of_stock_products = len([p for p in products if p.get('stock', 0) == 0 and p.get('active', True)])

    total_orders = len(orders)
    pending_orders = len([o for o in orders if o['status'] == 'pending'])

    return render_template('admin_dashboard.html',
                           total_products=total_products,
                           active_products=active_products,
                           low_stock_products=low_stock_products,
                           out_of_stock_products=out_of_stock_products,
                           total_orders=total_orders,
                           pending_orders=pending_orders)

@app.route('/admin/products')
def admin_products():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login_page'))

    products = load_products()
    return render_template('admin_products.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
def admin_add_product():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login_page'))

    if request.method == 'POST':
        products = load_products()

        new_product = {
            "id": get_next_product_id(),
            "name": request.form.get('name'),
            "brand": request.form.get('brand'),
            "price": float(request.form.get('price')),
            "original_price": float(request.form.get('original_price')),
            "discount": int(request.form.get('discount', 0)),
            "category": request.form.get('category'),
            "image": request.form.get('image'),
            "rating": float(request.form.get('rating', 4.0)),
            "reviews": int(request.form.get('reviews', 0)),
            "stock": int(request.form.get('stock')),
            "description": request.form.get('description'),
            "featured": 'featured' in request.form,
            "active": 'active' in request.form
        }

        products.append(new_product)
        save_products(products)
        return redirect(url_for('admin_products'))

    return render_template('admin_add_product.html')

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
def admin_edit_product(product_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login_page'))

    products = load_products()
    product = next((p for p in products if p['id'] == product_id), None)

    if not product:
        return "Product not found", 404

    if request.method == 'POST':
        product.update({
            "name": request.form.get('name'),
            "brand": request.form.get('brand'),
            "price": float(request.form.get('price')),
            "original_price": float(request.form.get('original_price')),
            "discount": int(request.form.get('discount', 0)),
            "category": request.form.get('category'),
            "image": request.form.get('image'),
            "rating": float(request.form.get('rating', 4.0)),
            "reviews": int(request.form.get('reviews', 0)),
            "stock": int(request.form.get('stock')),
            "description": request.form.get('description'),
            "featured": 'featured' in request.form,
            "active": 'active' in request.form
        })

        save_products(products)
        return redirect(url_for('admin_products'))

    return render_template('admin_edit_product.html', product=product)

@app.route('/admin/products/delete/<int:product_id>')
def admin_delete_product(product_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login_page'))

    products = load_products()
    products = [p for p in products if p['id'] != product_id]
    save_products(products)
    return redirect(url_for('admin_products'))

@app.route('/admin/stock')
def admin_stock_management():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login_page'))

    products = load_products()
    return render_template('admin_stock.html', products=products)

@app.route('/admin/stock/update', methods=['POST'])
def admin_update_stock():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login_page'))

    product_id = int(request.form.get('product_id'))
    new_stock = int(request.form.get('stock'))

    products = load_products()
    for product in products:
        if product['id'] == product_id:
            product['stock'] = new_stock
            break

    save_products(products)
    return redirect(url_for('admin_stock_management'))

@app.route('/admin/stock/bulk_update', methods=['POST'])
def admin_bulk_update_stock():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login_page'))

    products = load_products()
    for product in products:
        stock_field = f"stock_{product['id']}"
        if stock_field in request.form:
            product['stock'] = int(request.form[stock_field])

    save_products(products)
    return redirect(url_for('admin_stock_management'))

@app.route('/admin/orders')
def admin_orders():
    """Admin order management page"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login_page'))

    orders = load_orders()
    return render_template('admin_orders.html', orders=orders)

@app.route('/admin/orders/update_status', methods=['POST'])
def update_order_status():
    """Update order status"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Not authorized'})

    order_id = int(request.form.get('order_id'))
    new_status = request.form.get('status')

    orders = load_orders()
    for order in orders:
        if order['id'] == order_id:
            order['status'] = new_status
            if new_status == 'delivered':
                order['delivery_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            break

    save_orders(orders)
    return jsonify({'success': True, 'message': 'Order status updated'})

@app.route('/admin/orders/<int:order_id>')
def admin_order_detail(order_id):
    """Admin order detail page"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login_page'))

    orders = load_orders()
    order = next((o for o in orders if o['id'] == order_id), None)

    if not order:
        return "Order not found", 404

    return render_template('admin_order_detail.html', order=order)

# Business Management Routes
@app.route('/admin/business')
def admin_business_dashboard():
    """Business management dashboard"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login_page'))

    financial_report = get_financial_reports()
    orders = load_orders()
    expenses = load_expenses()
    employees = load_employees()

    # Recent activity
    recent_orders = sorted(orders, key=lambda x: x['order_date'], reverse=True)[:5]
    recent_expenses = sorted(expenses, key=lambda x: x['date'], reverse=True)[:5]

    return render_template('admin_business.html',
                           report=financial_report,
                           recent_orders=recent_orders,
                           recent_expenses=recent_expenses,
                           employees=employees)

@app.route('/admin/financial-reports')
def admin_financial_reports():
    """Detailed financial reports"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login_page'))

    financial_report = get_financial_reports()
    orders = load_orders()
    expenses = load_expenses()

    # Monthly breakdown for charts
    monthly_data = []
    for i in range(6):
        month = (datetime.now().replace(day=1) - timedelta(days=30 * i)).strftime("%Y-%m")
        month_orders = [o for o in orders if o['order_date'].startswith(month)]
        month_expenses = [e for e in expenses if e['date'].startswith(month)]

        revenue = sum(o['total_amount'] for o in month_orders)
        expense = sum(e['amount'] for e in month_expenses)
        profit = revenue - expense

        monthly_data.append({
            'month': month,
            'revenue': revenue,
            'expenses': expense,
            'profit': profit
        })

    monthly_data.reverse()

    return render_template('admin_financial_reports.html',
                           report=financial_report,
                           monthly_data=monthly_data,
                           orders=orders,
                           expenses=expenses)

@app.route('/admin/employees')
def admin_employees():
    """Employee management"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login_page'))

    employees = load_employees()
    return render_template('admin_employees.html', employees=employees)

@app.route('/admin/employees/add', methods=['GET', 'POST'])
def admin_add_employee():
    """Add new employee"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login_page'))

    if request.method == 'POST':
        employees = load_employees()

        new_employee = {
            "id": max([e['id'] for e in employees], default=0) + 1,
            "name": request.form.get('name'),
            "position": request.form.get('position'),
            "salary": float(request.form.get('salary')),
            "email": request.form.get('email'),
            "phone": request.form.get('phone'),
            "hire_date": request.form.get('hire_date'),
            "status": request.form.get('status', 'active')
        }

        employees.append(new_employee)
        save_employees(employees)
        return redirect(url_for('admin_employees'))

    return render_template('admin_add_employee.html')

@app.route('/debug_session')
def debug_session():
    session['test'] = 'session_works'
    session.modified = True
    return jsonify({
        'session_id': session.sid,
        'session_data': dict(session),
        'cart': session.get('cart', {})
    })

@app.route('/admin/employees/edit/<int:employee_id>', methods=['GET', 'POST'])
def admin_edit_employee(employee_id):
    """Edit employee"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login_page'))

    employees = load_employees()
    employee = next((e for e in employees if e['id'] == employee_id), None)

    if not employee:
        return "Employee not found", 404

    if request.method == 'POST':
        employee.update({
            "name": request.form.get('name'),
            "position": request.form.get('position'),
            "salary": float(request.form.get('salary')),
            "email": request.form.get('email'),
            "phone": request.form.get('phone'),
            "hire_date": request.form.get('hire_date'),
            "status": request.form.get('status', 'active')
        })

        save_employees(employees)
        return redirect(url_for('admin_employees'))

    return render_template('admin_edit_employee.html', employee=employee)


@app.route('/admin/expenses')
def admin_expenses():
    """Expense management"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login_page'))

    # Forcer des données de test
    test_expenses = [
        {
            "id": 1,
            "date": "2024-03-01",
            "category": "Test",
            "description": "Test Expense",
            "amount": 100,
            "payment_method": "cash"
        }
    ]

    return render_template('admin_expenses.html', expenses=test_expenses)



@app.route('/admin/expenses/add', methods=['GET', 'POST'])
def admin_add_expense():
    """Add new expense"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login_page'))

    if request.method == 'POST':
        expenses = load_expenses()

        new_expense = {
            "id": max([e['id'] for e in expenses], default=0) + 1,
            "date": request.form.get('date'),
            "category": request.form.get('category'),
            "description": request.form.get('description'),
            "amount": float(request.form.get('amount')),
            "payment_method": request.form.get('payment_method')
        }

        expenses.append(new_expense)
        save_expenses(expenses)
        return redirect(url_for('admin_expenses'))

    return render_template('admin_add_expense.html')

@app.route('/admin/payroll')
def admin_payroll():
    """Payroll management"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login_page'))

    employees = load_employees()
    return render_template('admin_payroll.html', employees=employees)

@app.route('/admin/export/report')
def admin_export_report():
    """Export financial report as CSV"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login_page'))

    financial_report = get_financial_reports()
    orders = load_orders()

    # Create CSV response
    output = []
    output.append(['Financial Report - BetterDeal', ''])
    output.append(['Generated', datetime.now().strftime("%Y-%m-%d %H:%M")])
    output.append([])
    output.append(['REVENUE', ''])
    output.append(['Current Month', f"${financial_report['revenue']['current']:.2f}"])
    output.append(['Last Month', f"${financial_report['revenue']['last']:.2f}"])
    output.append(['Growth', f"{financial_report['revenue']['growth']:.1f}%"])
    output.append([])
    output.append(['EXPENSES', ''])
    output.append(['Current Month', f"${financial_report['expenses']['current']:.2f}"])
    output.append(['Last Month', f"${financial_report['expenses']['last']:.2f}"])
    output.append([])
    output.append(['PROFIT', ''])
    output.append(['Current Month', f"${financial_report['profit']['current']:.2f}"])
    output.append(['Last Month', f"${financial_report['profit']['last']:.2f}"])
    output.append(['Growth', f"{financial_report['profit']['growth']:.1f}%"])

    # Convert to CSV string
    csv_string = '\n'.join([','.join(map(str, row)) for row in output])

    response = make_response(csv_string)
    response.headers["Content-Disposition"] = f"attachment; filename=financial_report_{datetime.now().strftime('%Y%m%d')}.csv"
    response.headers["Content-type"] = "text/csv"

    return response


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)