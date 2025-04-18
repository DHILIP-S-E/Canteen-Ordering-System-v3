import streamlit as st
from streamlit_autorefresh import st_autorefresh
from database.db_utils import DatabaseManager
from utils.payment import PaymentManager  # Uncomment this line
import sqlite3
import pandas as pd
from datetime import datetime
import json
import os
from components.ui import (
    display_menu, display_cart, display_order_status,
    display_order_history, display_analytics, display_notifications
)

# Configure Streamlit page
st.set_page_config(
    page_title="Smart Canteen System",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize auto-refresh (every 5 seconds)
def init_auto_refresh():
    if 'refresh_interval' not in st.session_state:
        st.session_state.refresh_interval = 5
    return st_autorefresh(interval=st.session_state.refresh_interval * 1000, key="data_refresh")

# Cache data functions
@st.cache_data(ttl=5) # Cache for 5 seconds
def get_cached_menu_items(_db):
    return _db.get_menu_items()

@st.cache_data(ttl=5) # Cache for 5 seconds
def get_cached_orders(_db, username=None):
    if username:
        return _db.get_user_orders(username)
    return _db.get_all_orders()

@st.cache_data(ttl=5)
def get_cached_notifications(_db, username):
    return _db.get_user_notifications(username)

# Initialize session state variables
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'cart' not in st.session_state:
    st.session_state.cart = []
# Add this new initialization
if 'db_connection' not in st.session_state:
    st.session_state.db_connection = DatabaseManager()

# Initialize food item form state variables
if 'food_name' not in st.session_state:
    st.session_state.food_name = ""
if 'food_price' not in st.session_state:
    st.session_state.food_price = 0.0
if 'food_category' not in st.session_state:
    st.session_state.food_category = "Breakfast"
if 'food_stock' not in st.session_state:
    st.session_state.food_stock = 0
if 'food_validity' not in st.session_state:
    st.session_state.food_validity = "daily"
if 'food_image' not in st.session_state:
    st.session_state.food_image = ""

# Database initialization
def init_db():
    try:
        with sqlite3.connect('database/canteen.db', timeout=30) as conn:
            c = conn.cursor()
            
            # Create users table
            c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL
                )
            ''')
            
            # Create food_items table
            c.execute('''
                CREATE TABLE IF NOT EXISTS food_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    category TEXT NOT NULL,
                    stock INTEGER NOT NULL,
                    validity_type TEXT NOT NULL,
                    image_url TEXT,
                    active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Create orders table
            c.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    items TEXT NOT NULL,
                    total_amount REAL NOT NULL,
                    payment_method TEXT NOT NULL,
                    payment_id TEXT,
                    status TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (username) REFERENCES users(username)
                )
            ''')

            # Create notifications table
            c.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    message TEXT NOT NULL,
                    is_read BOOLEAN DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (username) REFERENCES users(username)
                )
            ''')
            
            # Insert default users if not exists
            default_users = [
                ('admin', 'admin123', 'admin'),
                ('staff', 'staff123', 'staff'),
                ('student1', 'stu123', 'student')
            ]
            
            for user in default_users:
                c.execute('INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)',
                         user)
            
            conn.commit()
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        raise e

def login():
    st.title("🍽️ Smart Canteen System")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Login")
        
        # Use form to handle submission properly
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["Admin", "Staff", "Student"])
            
            submit_button = st.form_submit_button("Login")
            
            if submit_button:
                # Input validation
                username = username.strip() if username else ""
                password = password.strip() if password else ""
                role = role.lower()  # Convert role to lowercase
                
                # Validate inputs
                if not username:
                    st.error("Please enter your username")
                    return
                if not password:
                    st.error("Please enter your password")
                    return
                
                try:
                    conn = sqlite3.connect('database/canteen.db')
                    c = conn.cursor()
                    
                    # First check if user exists with the correct role
                    c.execute('SELECT * FROM users WHERE username=? AND role=?', (username, role))
                    user_exists = c.fetchone()
                    
                    if not user_exists:
                        st.error(f"No {role} account found with this username")
                        return
                    
                    # Now check password
                    c.execute('SELECT * FROM users WHERE username=? AND password=? AND role=?', 
                             (username, password, role))
                    user = c.fetchone()
                    
                    if user:
                        st.success("Login successful!")
                        st.session_state.authenticated = True
                        st.session_state.user_role = role
                        st.session_state.username = username
                        st.experimental_rerun()
                    else:
                        st.error("Incorrect password")
                        
                except sqlite3.Error as e:
                    st.error("Database error occurred. Please try again.")
                finally:
                    conn.close()

def logout():
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.session_state.username = None
    st.session_state.cart = []
    st.experimental_rerun()

def student_dashboard():
    st.title("Student Dashboard")
    
    # Get the database connection from session state
    db = st.session_state.db_connection
    payment = PaymentManager()
    
    # Initialize auto-refresh
    count = st_autorefresh(interval=5000, key="datarefresh")
    
    # Get menu items using cached function
    menu_items = get_cached_menu_items(db)
    
    # Sidebar with notifications
    with st.sidebar:
        st.title(f"Welcome, {st.session_state.username}")
        
        # Display notifications with improved UI
        st.subheader("📫 Notifications")
        notifications = get_cached_notifications(db, st.session_state.username)
        
        if notifications.empty:
            st.info("No new notifications")
        else:
            for _, notif in notifications.iterrows():
                if not notif.is_read:
                    st.success(notif.message)
                    if "food is ready" in notif.message.lower():
                        st.balloons()
                db.mark_notification_read(notif.id)
        
        if st.button("Logout"):
            logout()
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["🍽️ Order Food", "📱 Active Orders", "📜 Order History"])
    
    with tab1:
        st.subheader("Today's Menu")
        
        # Search and filter options
        col1, col2 = st.columns([2, 1])
        with col1:
            search = st.text_input("🔍 Search for food items...", "")
        with col2:
            category_filter = st.selectbox(
                "Category",
                ["All"] + list(menu_items['category'].unique())
            )
        
        # Filter menu items based on search and category
        if search:
            menu_items = menu_items[menu_items['name'].str.contains(search, case=False)]
        if category_filter != "All":
            menu_items = menu_items[menu_items['category'] == category_filter]
        
        def add_to_cart(item, quantity):
            cart_item = {
                'id': item['id'],
                'name': item['name'],
                'price': item['price'],
                'quantity': quantity,
                'image_url': item.get('image_url', '')
            }
            st.session_state.cart.append(cart_item)
            st.success(f"Added {quantity} x {item['name']} to cart")
        
        # Display menu with images
        display_menu(menu_items, add_to_cart)
        
        # Display cart
        st.markdown("---")
        
        def remove_from_cart(item):
            st.session_state.cart.remove(item)
        
        total = display_cart(st.session_state.cart, remove_from_cart)
        
        if st.session_state.cart:
            payment_method = st.radio(
                "💳 Payment Method",
                ["Cash on Delivery", "Razorpay"]
            )
            
            if st.button("🛍️ Place Order"):
                if payment_method == "Razorpay":
                    payment_response = payment.process_payment(total)
                    if payment_response['status'] == 'success':
                        order_id = db.create_order(
                            st.session_state.username,
                            st.session_state.cart,
                            total,
                            'razorpay',
                            payment_response['payment_id']
                        )
                else:
                    order_id = db.create_order(
                        st.session_state.username,
                        st.session_state.cart,
                        total,
                        'cod'
                    )
                
                # Update stock
                for item in st.session_state.cart:
                    db.update_stock(item['id'], item['quantity'])
                
                # Add order placed notification
                db.add_notification(
                    st.session_state.username,
                    f"Your order #{order_id} has been placed successfully!"
                )
                
                st.session_state.cart = []
                st.success(f"Order placed successfully! Order ID: {order_id}")
                st.experimental_rerun()
    
    with tab2:
        st.subheader("Track Your Orders")
        active_orders = get_cached_orders(db, st.session_state.username)
        active_orders = active_orders[active_orders['status'] != 'prepared']
        
        if not active_orders.empty:
            for _, order in active_orders.iterrows():
                status = order['status']
                if status == 'prepared':
                    st.success(f"✅ Order #{order['order_id']} is ready! Please collect from counter.")
                elif status == 'preparing':
                    st.info(f"👨‍🍳 Order #{order['order_id']} is being prepared...")
                else:
                    st.warning(f"⏳ Order #{order['order_id']} is placed and waiting...")
        else:
            st.info("No active orders")
    
    with tab3:
        st.subheader("Your Order History")
        orders = db.get_user_orders(st.session_state.username)
        display_order_history(orders)

def staff_dashboard():
    st.title("Staff Dashboard")
    
    # Initialize auto-refresh
    count = st_autorefresh(interval=5000, key="staffrefresh")
    
    # Initialize database manager
    db = DatabaseManager()
    
    # Sidebar
    with st.sidebar:
        st.title(f"Welcome, {st.session_state.username}")
        if st.button("Logout"):
            logout()
    
    # Main content
    st.subheader("Incoming Orders")
    
    # Get all orders that are not completed
    orders = get_cached_orders(db)
    active_orders = orders[orders['status'] != 'prepared']
    
    if active_orders.empty:
        st.info("No active orders")
    else:
        for _, order in active_orders.iterrows():
            with st.expander(f"Order #{order['order_id']} - {order['timestamp']}"):
                st.write(f"**Customer:** {order['username']}")
                st.write(f"**Payment:** {order['payment_method']}")
                st.write(f"**Amount:** ₹{order['total_amount']:.2f}")
                
                # Display items
                items = pd.read_json(order['items'])
                st.write("**Items:**")
                for _, item in items.iterrows():
                    st.write(f"- {item['quantity']}x {item['name']}")
                
                # Status update buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if order['status'] != 'placed' and st.button('Mark as Placed', key=f"placed_{order['order_id']}"):
                        db.update_order_status(order['order_id'], 'placed')
                        st.experimental_rerun()
                
                with col2:
                    if order['status'] != 'preparing' and st.button('Mark as Preparing', key=f"preparing_{order['order_id']}"):
                        db.update_order_status(order['order_id'], 'preparing')
                        st.experimental_rerun()
                
                # When marking as prepared, send notification
                with col3:
                    if order['status'] != 'prepared' and st.button('Mark as Prepared', key=f"prepared_{order['order_id']}"):
                        db.update_order_status(order['order_id'], 'prepared')
                        # Add notification for student
                        db.add_notification(
                            order['username'],
                            f"✅ Your food for Order #{order['order_id']} is ready! Please collect at counter."
                        )
                        st.experimental_rerun()
    
    # Completed orders
    st.markdown("---")
    st.subheader("Completed Orders")
    completed_orders = orders[orders['status'] == 'prepared']
    
    if completed_orders.empty:
        st.info("No completed orders")
    else:
        for _, order in completed_orders.iterrows():
            with st.expander(f"Order #{order['order_id']} - {order['timestamp']}"):
                st.write(f"**Customer:** {order['username']}")
                st.write(f"**Payment:** {order['payment_method']}")
                st.write(f"**Amount:** ₹{order['total_amount']:.2f}")
                items = pd.read_json(order['items'])
                st.write("**Items:**")
                for _, item in items.iterrows():
                    st.write(f"- {item['quantity']}x {item['name']}")

def admin_dashboard():
    st.title("Admin Dashboard")
    
    # Initialize auto-refresh
    init_auto_refresh()
    
    # Initialize database manager
    db = DatabaseManager()
    
    # Sidebar
    with st.sidebar:
        st.title(f"Welcome, {st.session_state.username}")
        if st.button("Logout"):
            logout()
    
    # Main content tabs
    tabs = st.tabs(["User Management", "Food Items", "Analytics"])
    
    with tabs[0]:
        st.subheader("User Management")
        
        # Add new user
        with st.expander("Add New User"):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", ["admin", "staff", "student"])
            
            if st.button("Add User"):
                conn = sqlite3.connect('database/canteen.db')
                c = conn.cursor()
                try:
                    c.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                            (new_username, new_password, new_role))
                    conn.commit()
                    st.success("User added successfully!")
                except sqlite3.IntegrityError:
                    st.error("Username already exists!")
                conn.close()
                st.experimental_rerun()
        
        # List and manage users
        conn = sqlite3.connect('database/canteen.db')
        users = pd.read_sql_query('SELECT * FROM users', conn)
        conn.close()
        
        st.write("### Current Users")
        for _, user in users.iterrows():
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"**{user['username']}** ({user['role']})")
            
            with col2:
                if st.button("Reset Password", key=f"reset_{user['username']}"):
                    conn = sqlite3.connect('database/canteen.db')
                    c = conn.cursor()
                    c.execute('UPDATE users SET password = ? WHERE username = ?',
                            ('password123', user['username']))
                    conn.commit()
                    conn.close()
                    st.success(f"Password reset for {user['username']}")
            
            with col3:
                if user['username'] not in ['admin', 'staff', 'student1']:
                    if st.button("Delete", key=f"delete_{user['username']}"):
                        conn = sqlite3.connect('database/canteen.db')
                        c = conn.cursor()
                        c.execute('DELETE FROM users WHERE username = ?',
                                (user['username'],))
                        conn.commit()
                        conn.close()
                        st.experimental_rerun()
    
    with tabs[1]:
        st.subheader("Food Items Management")
        
        # Add new food item section
        with st.expander("Add New Food Item"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Item Name", key="new_name", value=st.session_state.food_name)
                price = st.number_input("Price (₹)", key="new_price", value=st.session_state.food_price, min_value=0.0, step=0.5)
                category = st.selectbox("Category", 
                                      ["Breakfast", "Lunch", "Snacks", "Beverages"],
                                      key="new_category",
                                      index=["Breakfast", "Lunch", "Snacks", "Beverages"].index(st.session_state.food_category))
            with col2:
                stock = st.number_input("Initial Stock", key="new_stock", value=st.session_state.food_stock, min_value=0)
                validity_type = st.selectbox("Validity Type", 
                                           ["daily", "regular"],
                                           key="new_validity",
                                           index=["daily", "regular"].index(st.session_state.food_validity))
                image_url = st.text_input("Image URL (optional)", 
                                        key="new_image",
                                        value=st.session_state.food_image)
            
            if st.button("Add Item"):
                if name and price > 0:
                    # Save current values to session state
                    st.session_state.food_name = name
                    st.session_state.food_price = price
                    st.session_state.food_category = category
                    st.session_state.food_stock = stock
                    st.session_state.food_validity = validity_type
                    st.session_state.food_image = image_url
                    
                    # Add the item
                    db.add_food_item(name, price, category, stock, validity_type, image_url)
                    st.success("Item added successfully!")
                    
                    # Only clear form after successful addition
                    st.session_state.food_name = ""
                    st.session_state.food_price = 0.0
                    st.session_state.food_category = "Breakfast"
                    st.session_state.food_stock = 0
                    st.session_state.food_validity = "daily"
                    st.session_state.food_image = ""
                    st.experimental_rerun()
                else:
                    st.error("Please enter a valid name and price")
                    # Keep the existing values in session state
        
        # List and manage food items
        menu_items = db.get_menu_items()
        
        st.write("### Current Menu Items")
        for _, item in menu_items.iterrows():
            with st.expander(f"{item['name']} ({item['category']})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Price:** ₹{item['price']:.2f}")
                    st.write(f"**Stock:** {item['stock']}")
                    st.write(f"**Type:** {item['validity_type']}")
                
                with col2:
                    new_stock = st.number_input("Update Stock",
                                              min_value=0,
                                              value=item['stock'],
                                              key=f"stock_{item['id']}")
                    new_image = st.text_input("Update Image URL",
                                            value=item.get('image_url', ''),
                                            key=f"image_{item['id']}")
                    
                    if st.button("Update", key=f"update_{item['id']}"):
                        db.update_food_item(
                            item['id'],
                            item['name'],
                            item['price'],
                            item['category'],
                            new_stock,
                            item['validity_type'],
                            new_image
                        )
                        st.success("Item updated!")
                        st.experimental_rerun()
                    
                    if st.button("Delete Item", key=f"delete_item_{item['id']}"):
                        db.delete_food_item(item['id'])
                        st.success("Item deleted!")
                        st.experimental_rerun()
        
        # Reset daily items
        st.markdown("---")
        if st.button("Reset Daily Items"):
            db.reset_daily_items()
            st.success("Daily items reset successfully!")
            st.experimental_rerun()
    
    with tabs[2]:
        st.subheader("Order Analytics")
        
        analytics = db.get_analytics()
        
        # Display analytics
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Orders", analytics['total_orders'])
            
            st.write("### Payment Methods")
            payment_stats = analytics['payment_stats']
            if not payment_stats.empty:
                st.bar_chart(payment_stats.set_index('payment_method'))
        
        with col2:
            st.write("### Most Sold Items")
            most_sold = analytics['most_sold']
            if not most_sold.empty:
                st.bar_chart(most_sold.set_index('items'))
        
        # Export data
        if st.button("Export Orders CSV"):
            orders = db.get_all_orders()
            orders.to_csv('orders_export.csv', index=False)
            st.success("Orders exported to orders_export.csv")

def main():
    # Initialize database
    if not os.path.exists('database'):
        os.makedirs('database')
    init_db()
    
    # Ensure database connection is initialized in session state
    if 'db_connection' not in st.session_state:
        st.session_state.db_connection = DatabaseManager()
    
    # Main application logic
    if not st.session_state.authenticated:
        login()
    else:
        user_role = st.session_state.user_role.lower()
        if user_role == 'student':
            student_dashboard()
        elif user_role == 'staff':
            staff_dashboard()
        elif user_role == 'admin':
            admin_dashboard()

if __name__ == "__main__":
    main()









