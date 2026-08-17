import sqlite3
import os

DB_NAME = "food_ordering.db"

def get_connection():
    """
    Creates and returns a connection to the SQLite database.
    row_factory = sqlite3.Row lets us access query results like dictionaries.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initializes the database:
    1. Creates the menu table with rich fields
    2. Creates the orders table with customer details & payment fields
    3. Creates settings table for restaurant UPI and payment configs
    4. Seeds sample menu items if empty or upgrades existing schema
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # ---------- MENU TABLE ----------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS menu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        is_veg INTEGER NOT NULL DEFAULT 1,
        description TEXT,
        rating REAL DEFAULT 4.5,
        image_url TEXT,
        available INTEGER NOT NULL DEFAULT 1
    )
    """)
    
    cursor.execute("PRAGMA table_info(menu)")
    menu_columns = [col[1] for col in cursor.fetchall()]
    if "is_veg" not in menu_columns:
        cursor.execute("ALTER TABLE menu ADD COLUMN is_veg INTEGER NOT NULL DEFAULT 1")
    if "description" not in menu_columns:
        cursor.execute("ALTER TABLE menu ADD COLUMN description TEXT")
    if "rating" not in menu_columns:
        cursor.execute("ALTER TABLE menu ADD COLUMN rating REAL DEFAULT 4.5")
    if "image_url" not in menu_columns:
        cursor.execute("ALTER TABLE menu ADD COLUMN image_url TEXT")

    # ---------- ORDERS TABLE ----------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        items TEXT NOT NULL,
        subtotal REAL NOT NULL DEFAULT 0.0,
        discount REAL NOT NULL DEFAULT 0.0,
        total REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'Preparing',
        customer_name TEXT DEFAULT '',
        customer_phone TEXT DEFAULT '',
        delivery_address TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        promo_code TEXT DEFAULT '',
        payment_method TEXT DEFAULT 'Cash on Delivery',
        payment_status TEXT DEFAULT 'Pending',
        transaction_id TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("PRAGMA table_info(orders)")
    order_columns = [col[1] for col in cursor.fetchall()]
    if "subtotal" not in order_columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN subtotal REAL NOT NULL DEFAULT 0.0")
    if "discount" not in order_columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN discount REAL NOT NULL DEFAULT 0.0")
    if "customer_name" not in order_columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN customer_name TEXT DEFAULT ''")
    if "customer_phone" not in order_columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN customer_phone TEXT DEFAULT ''")
    if "delivery_address" not in order_columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN delivery_address TEXT DEFAULT ''")
    if "notes" not in order_columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN notes TEXT DEFAULT ''")
    if "promo_code" not in order_columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN promo_code TEXT DEFAULT ''")
    if "payment_method" not in order_columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN payment_method TEXT DEFAULT 'Cash on Delivery'")
    if "payment_status" not in order_columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN payment_status TEXT DEFAULT 'Pending'")
    if "transaction_id" not in order_columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN transaction_id TEXT DEFAULT ''")
    if "created_at" not in order_columns:
        cursor.execute("ALTER TABLE orders ADD COLUMN created_at TEXT")

    # ---------- SETTINGS TABLE (RESTAURANT PAYMENT & QR CONFIGS) ----------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """)

    default_settings = {
        "upi_id": "aahara@upi",
        "merchant_name": "Aahara Foods Pvt Ltd",
        "bank_name": "HDFC Bank - Cyber City Branch",
        "account_number": "987654321098",
        "ifsc_code": "HDFC0001234",
        "qr_image_url": "https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=upi%3A%2F%2Fpay%3Fpa%3Daahara%40upi%26pn%3DAahara%2520Restaurant%26cu%3DINR"
    }

    for k, v in default_settings.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    # ---------- RICH SAMPLE MENU DATA ----------
    cursor.execute("SELECT COUNT(*) FROM menu")
    count = cursor.fetchone()[0]
    
    sample_menu = [
        ("Margherita Pizza", "Pizza", 299.0, 1, "Classic Mozzarella, fresh basil & San Marzano tomato sauce", 4.8, "https://images.unsplash.com/photo-1604382354936-07c5d9983bd3?auto=format&fit=crop&w=500&q=80"),
        ("Farmhouse Pizza", "Pizza", 349.0, 1, "Crisp capsicum, sweet corn, mushrooms & juicy tomatoes", 4.6, "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=500&q=80"),
        ("Pepperoni Feast Pizza", "Pizza", 399.0, 0, "Double pepperoni & melted mozzarella with garlic herb crust", 4.9, "https://images.unsplash.com/photo-1628840042765-356cda07504e?auto=format&fit=crop&w=500&q=80"),
        ("Crispy Chicken Burger", "Burger", 199.0, 0, "Crispy fried chicken breast, brioche bun, spicy mayo & pickles", 4.7, "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=500&q=80"),
        ("Ultimate Veggie Burger", "Burger", 149.0, 1, "Spiced potato & herb patty with crisp lettuce & tangy sauce", 4.5, "https://images.unsplash.com/photo-1550547660-d9450f859349?auto=format&fit=crop&w=500&q=80"),
        ("Hyderabadi Chicken Biryani", "Biryani", 249.0, 0, "Slow-cooked aromatic basmati rice with marinated chicken & spices", 4.9, "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=500&q=80"),
        ("Paneer Dum Biryani", "Biryani", 219.0, 1, "Fragrant basmati rice layered with spiced paneer cubes & saffron", 4.6, "https://images.unsplash.com/photo-1642821373181-696a54913e93?auto=format&fit=crop&w=500&q=80"),
        ("Peri Peri Fries", "Sides", 99.0, 1, "Crispy golden French fries tossed in fiery peri-peri seasoning", 4.7, "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?auto=format&fit=crop&w=500&q=80"),
        ("Garlic Breadsticks", "Sides", 129.0, 1, "Freshly baked breadsticks brushed with garlic butter & herbs", 4.4, "https://images.unsplash.com/photo-1619895092538-128341789043?auto=format&fit=crop&w=500&q=80"),
        ("Chilled Coke (330ml)", "Drinks", 60.0, 1, "Refreshing ice-cold Coca-Cola can", 4.8, "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?auto=format&fit=crop&w=500&q=80"),
        ("Mango Lassi", "Drinks", 89.0, 1, "Rich & creamy yogurt drink blended with Alphonso mango pulp", 4.8, "https://images.unsplash.com/photo-1527661591475-527312dd65f5?auto=format&fit=crop&w=500&q=80"),
        ("Choco Lava Cake", "Desserts", 119.0, 1, "Warm chocolate cake with a molten chocolate fudge center", 4.9, "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?auto=format&fit=crop&w=500&q=80")
    ]
    
    if count < 10:
        cursor.execute("DELETE FROM menu")
        cursor.executemany(
            """INSERT INTO menu (name, category, price, is_veg, description, rating, image_url, available) 
               VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
            sample_menu
        )
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized and updated successfully.")
