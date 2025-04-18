import sqlite3
import pandas as pd
from datetime import datetime
import json
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path='database/canteen.db'):
        self.db_path = db_path
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=30)  # Increase timeout to 30 seconds
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def get_menu_items(self):
        with self.get_connection() as conn:
            query = '''
                SELECT * FROM food_items 
                WHERE active = 1 AND (stock > 0 OR validity_type = 'daily')
            '''
            return pd.read_sql_query(query, conn)
    
    def update_stock(self, item_id, quantity):
        with self.get_connection() as conn:
            c = conn.cursor()
            # First check the item's validity_type
            c.execute('SELECT validity_type FROM food_items WHERE id = ?', (item_id,))
            result = c.fetchone()
            if result:
                validity_type = result[0]
                if validity_type == 'daily':
                    # For daily items, just reduce the stock
                    c.execute('UPDATE food_items SET stock = stock - ? WHERE id = ?', 
                            (quantity, item_id))
                else:
                    # For regular items, reduce stock only if it's above 0
                    c.execute('''
                        UPDATE food_items 
                        SET stock = CASE
                            WHEN stock >= ? THEN stock - ?
                            ELSE stock
                        END
                        WHERE id = ?
                    ''', (quantity, quantity, item_id))
    
    def create_order(self, username, items, total_amount, payment_method, payment_id=None):
        with self.get_connection() as conn:
            c = conn.cursor()
            order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
            items_json = json.dumps(items)
            
            c.execute('''
                INSERT INTO orders (order_id, username, items, total_amount, 
                                  payment_method, payment_id, status)
                VALUES (?, ?, ?, ?, ?, ?, 'placed')
            ''', (order_id, username, items_json, total_amount, payment_method, payment_id))
            return order_id
    
    def get_user_orders(self, username):
        with self.get_connection() as conn:
            query = '''
                SELECT * FROM orders 
                WHERE username = ? 
                ORDER BY timestamp DESC
            '''
            return pd.read_sql_query(query, conn, params=[username])
    
    def get_all_orders(self, status=None):
        with self.get_connection() as conn:
            if status:
                query = 'SELECT * FROM orders WHERE status = ? ORDER BY timestamp DESC'
                return pd.read_sql_query(query, conn, params=[status])
            else:
                query = 'SELECT * FROM orders ORDER BY timestamp DESC'
                return pd.read_sql_query(query, conn)
    
    def update_order_status(self, order_id, status):
        with self.get_connection() as conn:
            c = conn.cursor()
            try:
                # Start a transaction
                c.execute('BEGIN')
                
                # Get the username associated with this order
                c.execute('SELECT username FROM orders WHERE order_id = ?', (order_id,))
                result = c.fetchone()
                
                if result:
                    username = result[0]
                    # Update the order status
                    c.execute('UPDATE orders SET status = ? WHERE order_id = ?', (status, order_id))
                    
                    # Add a notification for the user
                    status_messages = {
                        'placed': 'Your order has been received and will be prepared soon!',
                        'preparing': 'Your order is now being prepared in the kitchen.',
                        'prepared': 'Your order is ready for pickup!'
                    }
                    
                    message = f"Order #{order_id}: {status_messages.get(status, 'Status updated')}"
                    
                    # Add notification within the same transaction
                    c.execute('''
                        INSERT INTO notifications (username, message)
                        VALUES (?, ?)
                    ''', (username, message))
                    
                # Commit the transaction
                c.execute('COMMIT')
            except sqlite3.Error as e:
                # Rollback in case of error
                c.execute('ROLLBACK')
                raise e
    
    def add_food_item(self, name, price, category, stock, validity_type, image_url=None):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO food_items (name, price, category, stock, validity_type, image_url)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, price, category, stock, validity_type, image_url))
    
    def update_food_item(self, item_id, name, price, category, stock, validity_type, image_url=None):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                UPDATE food_items 
                SET name = ?, price = ?, category = ?, stock = ?, validity_type = ?, image_url = ?
                WHERE id = ?
            ''', (name, price, category, stock, validity_type, image_url, item_id))
    
    def delete_food_item(self, item_id):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute('UPDATE food_items SET active = 0 WHERE id = ?', (item_id,))
    
    def reset_daily_items(self):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute("UPDATE food_items SET stock = 0 WHERE validity_type = 'daily'")
    
    def get_analytics(self):
        with self.get_connection() as conn:
            # Total orders
            total_orders = pd.read_sql_query(
                'SELECT COUNT(*) as total FROM orders', conn).iloc[0]['total']
            
            # Payment method stats
            payment_stats = pd.read_sql_query('''
                SELECT payment_method, COUNT(*) as count 
                FROM orders GROUP BY payment_method
            ''', conn)
            
            # Most sold items
            most_sold = pd.read_sql_query('''
                SELECT items, COUNT(*) as count 
                FROM orders GROUP BY items 
                ORDER BY count DESC LIMIT 5
            ''', conn)
            
            return {
                'total_orders': total_orders,
                'payment_stats': payment_stats,
                'most_sold': most_sold
            }
    
    def add_notification(self, username, message):
        with self.get_connection() as conn:
            c = conn.cursor()
            try:
                c.execute('BEGIN')
                c.execute('''
                    INSERT INTO notifications (username, message)
                    VALUES (?, ?)
                ''', (username, message))
                c.execute('COMMIT')
            except sqlite3.Error as e:
                c.execute('ROLLBACK')
                raise e

    def get_user_notifications(self, username):
        with self.get_connection() as conn:
            query = '''
                SELECT id, username, message, COALESCE(is_read, 0) as is_read, timestamp
                FROM notifications 
                WHERE username = ?
                ORDER BY timestamp DESC
            '''
            return pd.read_sql_query(query, conn, params=[username])

    def mark_notification_read(self, notification_id):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute('UPDATE notifications SET is_read = 1 WHERE id = ?', (notification_id,))
