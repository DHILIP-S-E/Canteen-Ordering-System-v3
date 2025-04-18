import streamlit as st
import pandas as pd
from datetime import datetime

def display_menu(menu_items, add_to_cart_callback):
    # Create a grid layout for menu items
    cols = st.columns(3)
    
    for idx, item in menu_items.iterrows():
        with cols[idx % 3]:
            # Create card-like container
            with st.container():
                st.subheader(item['name'])
                
                # Display image if available
                image_url = item.get('image_url', '')
                if image_url:
                    try:
                        st.image(
                            image_url,
                            width=200,  # Fixed width instead of container width
                            caption=None
                        )
                    except Exception:
                        st.warning("⚠️ Image not available")
                
                # Display item details
                st.write(f"**Price:** ₹{item['price']:.2f}")
                st.write(f"**Category:** {item['category']}")
                st.write(f"**Stock:** {item['stock']}")
                
                # Add to cart section
                if item['stock'] > 0:
                    quantity = st.number_input(
                        "Quantity",
                        min_value=1,
                        max_value=item['stock'],
                        value=1,
                        key=f"qty_{item['id']}"
                    )
                    if st.button("Add to Cart", key=f"add_{item['id']}"):
                        add_to_cart_callback(item, quantity)
                else:
                    st.error("Out of stock!")
                
                st.markdown("---")

def display_cart(cart_items, on_remove):
    """Display shopping cart"""
    st.markdown("""
        <style>
        .cart-item {
            border: 1px solid #eee;
            border-radius: 8px;
            padding: 0.8rem;
            margin: 0.5rem 0;
            background-color: white;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .cart-total {
            background-color: #2ecc71;
            color: white;
            padding: 1rem;
            border-radius: 8px;
            margin-top: 1rem;
            font-size: 1.2rem;
            font-weight: bold;
            text-align: center;
        }
        .cart-empty {
            text-align: center;
            padding: 2rem;
            color: #7f8c8d;
            background-color: #f9f9f9;
            border-radius: 8px;
            margin: 1rem 0;
        }
        </style>
    """, unsafe_allow_html=True)

    if not cart_items:
        st.markdown("""
            <div class="cart-empty">
                <h3>🛒 Your cart is empty</h3>
                <p>Add some delicious items to get started!</p>
            </div>
        """, unsafe_allow_html=True)
        return 0
    
    st.markdown("### 🛒 Your Cart")
    total = 0
    
    for item in cart_items:
        total += item['price'] * item['quantity']
        
        st.markdown(f"""
            <div class="cart-item">
                <div>
                    <strong>{item['name']}</strong><br>
                    <small>Quantity: {item['quantity']} × ₹{item['price']:.2f}</small>
                </div>
                <div>
                    <strong>₹{(item['price'] * item['quantity']):.2f}</strong>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Remove button in a more subtle position
        col1, col2, col3 = st.columns([6, 2, 2])
        with col3:
            if st.button("🗑️ Remove", key=f"remove_{item['id']}"):
                on_remove(item)
    
    # Display total with animation
    st.markdown(f"""
        <div class="cart-total">
            Total Amount: ₹{total:.2f}
        </div>
    """, unsafe_allow_html=True)
    
    return total

def display_order_status(order_id, status):
    """Display order status with color coding and modern design"""
    st.markdown("""
        <style>
        .order-status {
            padding: 1.5rem;
            border-radius: 12px;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin: 1rem 0;
        }
        .status-badge {
            display: inline-block;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            color: white;
            font-weight: bold;
            margin: 0.5rem 0;
        }
        .status-placed {
            background: #f1c40f;
        }
        .status-preparing {
            background: #e67e22;
        }
        .status-prepared {
            background: #2ecc71;
        }
        .order-id {
            color: #34495e;
            font-size: 1.2rem;
            margin-bottom: 0.5rem;
        }
        .status-message {
            margin-top: 1rem;
            padding: 1rem;
            border-radius: 8px;
            background: #f8f9fa;
        }
        </style>
    """, unsafe_allow_html=True)
    
    status_colors = {
        'placed': 'status-placed',
        'preparing': 'status-preparing',
        'prepared': 'status-prepared'
    }
    
    status_messages = {
        'placed': '🎯 Order placed successfully! We\'ll start preparing it soon.',
        'preparing': '👨‍🍳 Our chefs are working their magic on your order...',
        'prepared': '✨ Your order is ready! Please collect it from the counter.'
    }
    
    status_class = status_colors.get(status, '')
    message = status_messages.get(status, 'Status unknown')
    
    st.markdown(f"""
        <div class="order-status">
            <div class="order-id">Order #{order_id}</div>
            <div class="status-badge {status_class}">
                {status.title()}
            </div>
            <div class="status-message">
                {message}
            </div>
        </div>
    """, unsafe_allow_html=True)

def display_order_history(orders):
    """Display order history with modern card design"""
    st.markdown("""
        <style>
        .history-card {
            background: white;
            border-radius: 10px;
            padding: 1.2rem;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border: 1px solid #eee;
        }
        .history-card:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            transform: translateY(-2px);
            transition: all 0.3s ease;
        }
        .history-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #eee;
        }
        .history-items {
            margin: 1rem 0;
            padding: 0.8rem;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .history-total {
            text-align: right;
            font-size: 1.1rem;
            color: #2ecc71;
            font-weight: bold;
        }
        .history-empty {
            text-align: center;
            padding: 3rem;
            background: #f8f9fa;
            border-radius: 10px;
            color: #7f8c8d;
        }
        .payment-badge {
            display: inline-block;
            padding: 0.3rem 0.8rem;
            border-radius: 15px;
            font-size: 0.9rem;
            background: #e8f5e9;
            color: #2e7d32;
        }
        </style>
    """, unsafe_allow_html=True)
    
    if orders.empty:
        st.markdown("""
            <div class="history-empty">
                <h3>📜 No Order History</h3>
                <p>Your past orders will appear here once you start ordering.</p>
            </div>
        """, unsafe_allow_html=True)
        return
    
    for _, order in orders.iterrows():
        items = pd.read_json(order['items'])
        timestamp = pd.to_datetime(order['timestamp']).strftime("%d/%m/%Y %H:%M")
        
        st.markdown(f"""
            <div class="history-card">
                <div class="history-header">
                    <div>
                        <strong>Order #{order['order_id']}</strong><br>
                        <small>{timestamp}</small>
                    </div>
                    <div class="payment-badge">
                        {order['payment_method'].upper()}
                    </div>
                </div>
                
                <div class="history-items">
                    <strong>Items:</strong><br>
        """, unsafe_allow_html=True)
        
        # Display items
        for _, item in items.iterrows():
            st.markdown(f"""
                • {item['quantity']}× {item['name']} 
                <span style="float: right">₹{item['price'] * item['quantity']:.2f}</span><br>
            """, unsafe_allow_html=True)
        
        st.markdown(f"""
                </div>
                <div class="history-total">
                    Total Amount: ₹{order['total_amount']:.2f}
                </div>
            </div>
        """, unsafe_allow_html=True)

def display_analytics(analytics_data):
    """Display analytics dashboard"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Orders", analytics_data['total_orders'])
        
        st.write("### Payment Methods")
        st.bar_chart(analytics_data['payment_stats'].set_index('payment_method'))
    
    with col2:
        st.write("### Most Sold Items")
        st.bar_chart(analytics_data['most_sold'].set_index('items'))

def display_notifications(notifications, mark_as_read_callback):
    """Display notifications with improved organization and styling"""
    st.markdown("""
        <style>
        .notification-card {
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 8px;
            background: white;
            border-left: 4px solid #2196F3;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        .notification-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        .notification-time {
            color: #666;
            font-size: 0.8rem;
            margin-top: 0.5rem;
        }
        .unread {
            background: #E3F2FD;
            border-left-color: #1976D2;
        }
        .notification-badge {
            position: absolute;
            top: -5px;
            right: -5px;
            background: #ff4444;
            color: white;
            border-radius: 50%;
            padding: 0.2rem 0.5rem;
            font-size: 0.8rem;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

    if notifications.empty:
        st.info("No notifications")
        return

    # Sort notifications: unread first, then by timestamp
    notifications = notifications.sort_values(['is_read', 'timestamp'], ascending=[True, False])
    
    # Count unread notifications
    unread_count = len(notifications[notifications['is_read'] == 0])
    
    if unread_count > 0:
        st.markdown(f"<div style='position: relative; display: inline-block;'>🔔 New Notifications<span class='notification-badge'>{unread_count}</span></div>", unsafe_allow_html=True)
    
    for _, notif in notifications.iterrows():
        with st.container():
            is_unread = not notif['is_read']
            card_class = "notification-card unread" if is_unread else "notification-card"
            timestamp = pd.to_datetime(notif['timestamp']).strftime("%B %d, %Y at %I:%M %p")
            
            st.markdown(f"""
                <div class="{card_class}">
                    {notif['message']}
                    <div class="notification-time">
                        {timestamp}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if is_unread and st.button("✓ Mark as Read", key=f"read_{notif['id']}", 
                                     help="Click to mark this notification as read"):
                mark_as_read_callback(notif['id'])
                st.rerun()



