import json
import datetime
from database import get_connection

cart = []
applied_promo = {"code": "", "discount": 0.0}

VALID_PROMOS = {
    "AAHARA10": {"type": "percent", "value": 10, "desc": "10% OFF on all orders"},
    "WELCOME50": {"type": "flat", "value": 50, "desc": "₹50 OFF on orders above ₹200"}
}

def search_menu(query=None, is_veg=None, max_price=None):
    """
    Searches the menu with filters: keyword, vegetarian (is_veg=True/False), and price limit (max_price).
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    q_clean = (query or "").strip().lower()
    conditions = ["available = 1"]
    params = []

    if q_clean and q_clean not in ("all", "menu", "full", "list", "show", "everything", "entire", "*"):
        conditions.append("(LOWER(name) LIKE ? OR LOWER(category) LIKE ?)")
        params.extend([f"%{q_clean}%", f"%{q_clean}%"])

    if is_veg is not None:
        veg_val = 1 if is_veg in (True, 1, "true", "1", "veg") else 0
        conditions.append("is_veg = ?")
        params.append(veg_val)

    if max_price is not None:
        try:
            mp = float(max_price)
            conditions.append("price <= ?")
            params.append(mp)
        except (ValueError, TypeError):
            pass

    where_clause = " AND ".join(conditions)
    sql = f"SELECT id, name, category, price, is_veg, description, rating, image_url, available FROM menu WHERE {where_clause} ORDER BY category, name"
    
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    
    results = [dict(row) for row in rows]
    if not results:
        filter_str = f"'{query}'" if query else "specified criteria"
        return {"found": False, "message": f"No menu items found matching {filter_str}."}
    
    return {"found": True, "count": len(results), "items": results}

def get_full_menu(include_unavailable=False):
    conn = get_connection()
    cursor = conn.cursor()
    if include_unavailable:
        cursor.execute("SELECT id, name, category, price, is_veg, description, rating, image_url, available FROM menu ORDER BY category, name")
    else:
        cursor.execute("SELECT id, name, category, price, is_veg, description, rating, image_url, available FROM menu WHERE available = 1 ORDER BY category, name")
    rows = cursor.fetchall()
    conn.close()
    items = [dict(r) for r in rows]
    return {"found": True, "count": len(items), "items": items}

def add_to_cart(item_id, quantity=1):
    try:
        item_id = int(item_id)
        quantity = int(quantity)
    except (ValueError, TypeError):
        return {"success": False, "message": "item_id and quantity must be valid numbers"}

    if quantity <= 0:
        return {"success": False, "message": "Quantity must be greater than 0"}
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM menu WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    conn.close()
    
    if item is None:
        return {"success": False, "message": f"Item with ID {item_id} not found"}
        
    if item["available"] == 0:
        return {"success": False, "message": f"'{item['name']}' is currently out of stock"}
        
    for cart_item in cart:
        if cart_item["id"] == item_id:
            cart_item["quantity"] += quantity
            return {
                "success": True,
                "message": f"Updated '{item['name']}' quantity to {cart_item['quantity']} in cart.",
                "cart": cart
            }
            
    cart.append({
        "id": item["id"],
        "name": item["name"],
        "price": item["price"],
        "is_veg": item["is_veg"],
        "quantity": quantity,
        "image_url": item["image_url"] if "image_url" in item.keys() else ""
    })
    
    return {
        "success": True,
        "message": f"Added {quantity} x '{item['name']}' (₹{item['price']}) to cart.",
        "cart": cart
    }

def remove_from_cart(item_id, quantity=None):
    try:
        item_id = int(item_id)
    except (ValueError, TypeError):
        return {"success": False, "message": "item_id must be an integer"}

    target_idx = None
    for idx, cart_item in enumerate(cart):
        if cart_item["id"] == item_id:
            target_idx = idx
            break
            
    if target_idx is None:
        return {"success": False, "message": f"Item ID {item_id} is not in your cart"}
        
    item_name = cart[target_idx]["name"]
    if quantity is None:
        del cart[target_idx]
        return {"success": True, "message": f"Removed '{item_name}' from cart.", "cart": cart}

    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        del cart[target_idx]
        return {"success": True, "message": f"Removed '{item_name}' from cart.", "cart": cart}

    if quantity >= cart[target_idx]["quantity"]:
        del cart[target_idx]
        return {"success": True, "message": f"Removed '{item_name}' from cart.", "cart": cart}
    else:
        cart[target_idx]["quantity"] -= quantity
        return {
            "success": True,
            "message": f"Reduced '{item_name}' quantity to {cart[target_idx]['quantity']}.",
            "cart": cart
        }

def update_cart_quantity(item_id, quantity):
    try:
        item_id = int(item_id)
        quantity = int(quantity)
    except (ValueError, TypeError):
        return {"success": False, "message": "item_id and quantity must be integers"}

    if quantity <= 0:
        return remove_from_cart(item_id)

    for cart_item in cart:
        if cart_item["id"] == item_id:
            cart_item["quantity"] = quantity
            return {
                "success": True,
                "message": f"Set '{cart_item['name']}' quantity to {quantity}.",
                "cart": cart
            }
            
    return {"success": False, "message": f"Item ID {item_id} is not in your cart"}

def clear_cart():
    cart.clear()
    applied_promo["code"] = ""
    applied_promo["discount"] = 0.0
    return {"success": True, "message": "Cart cleared successfully."}

def apply_promo_code(code):
    code_clean = (code or "").strip().upper()
    if not code_clean:
        applied_promo["code"] = ""
        applied_promo["discount"] = 0.0
        return {"success": True, "message": "Promo code removed.", "discount": 0.0}

    if code_clean not in VALID_PROMOS:
        return {
            "success": False,
            "message": f"Invalid promo code '{code_clean}'. Try 'AAHARA10' (10% OFF) or 'WELCOME50' (₹50 OFF)."
        }

    subtotal = sum(item["price"] * item["quantity"] for item in cart)
    if subtotal == 0:
        return {"success": False, "message": "Add items to your cart before applying a promo code."}

    promo = VALID_PROMOS[code_clean]
    if code_clean == "WELCOME50" and subtotal < 200:
        return {"success": False, "message": "WELCOME50 requires a minimum cart total of ₹200."}

    if promo["type"] == "percent":
        discount = round(subtotal * (promo["value"] / 100.0), 2)
    else:
        discount = float(min(promo["value"], subtotal))

    applied_promo["code"] = code_clean
    applied_promo["discount"] = discount
    
    return {
        "success": True,
        "code": code_clean,
        "discount": discount,
        "message": f"Promo code '{code_clean}' applied! Saved ₹{discount:.2f}. ({promo['desc']})"
    }

def view_cart():
    if not cart:
        return {"empty": True, "items": [], "subtotal": 0.0, "discount": 0.0, "tax": 0.0, "total": 0.0, "message": "Your cart is empty"}
        
    items_with_subtotal = []
    subtotal = 0.0
    for item in cart:
        item_subtotal = item["price"] * item["quantity"]
        subtotal += item_subtotal
        items_with_subtotal.append({
            "id": item["id"],
            "name": item["name"],
            "quantity": item["quantity"],
            "price": item["price"],
            "subtotal": item_subtotal,
            "is_veg": item.get("is_veg", 1),
            "image_url": item.get("image_url", "")
        })

    discount = 0.0
    code = applied_promo.get("code", "")
    if code in VALID_PROMOS:
        promo = VALID_PROMOS[code]
        if code == "WELCOME50" and subtotal < 200:
            applied_promo["code"] = ""
            applied_promo["discount"] = 0.0
        else:
            if promo["type"] == "percent":
                discount = round(subtotal * (promo["value"] / 100.0), 2)
            else:
                discount = float(min(promo["value"], subtotal))
            applied_promo["discount"] = discount

    tax = round((subtotal - discount) * 0.05, 2)
    total = round(max(0.0, subtotal - discount + tax), 2)
    
    return {
        "empty": False,
        "items": items_with_subtotal,
        "subtotal": subtotal,
        "promo_code": applied_promo.get("code", ""),
        "discount": discount,
        "tax": tax,
        "total": total
    }

def place_order(customer_name="", customer_phone="", delivery_address="", notes="", promo_code=None, payment_method="Cash on Delivery", transaction_id=""):
    cart_info = view_cart()
    if cart_info.get("empty"):
        return {"success": False, "message": "Cannot place order, your cart is empty"}

    if promo_code:
        apply_promo_code(promo_code)
        cart_info = view_cart()

    items_json = json.dumps(cart_info["items"])
    subtotal = cart_info["subtotal"]
    discount = cart_info["discount"]
    total = cart_info["total"]
    applied_code = cart_info.get("promo_code", "")
    created_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c_name = (customer_name or "").strip() or "Valued Customer"
    c_phone = (customer_phone or "").strip() or "N/A"
    c_addr = (delivery_address or "").strip() or "Dine-in / Standard Delivery"
    p_method = (payment_method or "").strip() or "Cash on Delivery"
    if p_method not in ("UPI", "Cash on Delivery"):
        p_method = "Cash on Delivery"

    p_status = "Paid (UPI)" if (p_method == "UPI" and (transaction_id or "").strip()) else ("Pending (UPI)" if p_method == "UPI" else "Pending (COD)")
    tx_id = (transaction_id or "").strip()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO orders (items, subtotal, discount, total, status, customer_name, customer_phone, delivery_address, notes, promo_code, payment_method, payment_status, transaction_id, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (items_json, subtotal, discount, total, "Preparing", c_name, c_phone, c_addr, notes or "", applied_code, p_method, p_status, tx_id, created_str)
    )
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()

    clear_cart()

    return {
        "success": True,
        "order_id": order_id,
        "customer_name": c_name,
        "customer_phone": c_phone,
        "delivery_address": c_addr,
        "subtotal": subtotal,
        "discount": discount,
        "total": total,
        "status": "Preparing",
        "payment_method": p_method,
        "payment_status": p_status,
        "transaction_id": tx_id,
        "notes": notes,
        "message": f"Order #{order_id} placed! Payment Method: {p_method} ({p_status}). Total: ₹{total:.2f}. Status: Preparing."
    }

def track_order(order_id):
    if not order_id:
        return {"found": False, "message": "order_id is required"}
    try:
        order_id = int(order_id)
    except (ValueError, TypeError):
        return {"found": False, "message": "order_id must be an integer"}
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()
    conn.close()
    
    if order is None:
        return {"found": False, "message": f"Order #{order_id} not found."}
        
    return {
        "found": True,
        "order_id": order["id"],
        "customer_name": order["customer_name"] if "customer_name" in order.keys() else "Customer",
        "customer_phone": order["customer_phone"] if "customer_phone" in order.keys() else "",
        "delivery_address": order["delivery_address"] if "delivery_address" in order.keys() else "",
        "subtotal": order["subtotal"] if "subtotal" in order.keys() else order["total"],
        "discount": order["discount"] if "discount" in order.keys() else 0.0,
        "total": order["total"],
        "status": order["status"],
        "payment_method": order["payment_method"] if "payment_method" in order.keys() else "Cash on Delivery",
        "payment_status": order["payment_status"] if "payment_status" in order.keys() else "Pending",
        "transaction_id": order["transaction_id"] if "transaction_id" in order.keys() else "",
        "notes": order["notes"] if "notes" in order.keys() else "",
        "created_at": order["created_at"] if "created_at" in order.keys() else "",
        "items": json.loads(order["items"])
    }

def get_order_history():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for r in rows:
        history.append({
            "order_id": r["id"],
            "customer_name": r["customer_name"] if "customer_name" in r.keys() else "Customer",
            "customer_phone": r["customer_phone"] if "customer_phone" in r.keys() else "",
            "delivery_address": r["delivery_address"] if "delivery_address" in r.keys() else "",
            "subtotal": r["subtotal"] if "subtotal" in r.keys() else r["total"],
            "discount": r["discount"] if "discount" in r.keys() else 0.0,
            "total": r["total"],
            "status": r["status"],
            "payment_method": r["payment_method"] if "payment_method" in r.keys() else "Cash on Delivery",
            "payment_status": r["payment_status"] if "payment_status" in r.keys() else "Pending",
            "transaction_id": r["transaction_id"] if "transaction_id" in r.keys() else "",
            "notes": r["notes"] if "notes" in r.keys() else "",
            "created_at": r["created_at"] if "created_at" in r.keys() else "",
            "items": json.loads(r["items"])
        })
        
    return {"count": len(history), "orders": history}

# ---------- RESTAURANT ADMIN TOOLING ----------

def update_order_status(order_id, new_status):
    """
    Updates status of an order following strict progression:
    Preparing -> Order Ready -> Out for Delivery -> Delivered (or Cancelled).
    Once delivered or cancelled, status cannot be changed again.
    """
    valid_statuses = ["Preparing", "Order Ready", "Out for Delivery", "Delivered", "Cancelled"]
    if new_status not in valid_statuses:
        return {"success": False, "message": f"Invalid status '{new_status}'. Allowed: {valid_statuses}"}

    try:
        order_id = int(order_id)
    except (ValueError, TypeError):
        return {"success": False, "message": "order_id must be an integer"}

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM orders WHERE id = ?", (order_id,))
    row = cursor.fetchone()
    
    if row is None:
        conn.close()
        return {"success": False, "message": f"Order #{order_id} not found."}

    curr_status = row["status"]

    # 1. Lock check: If already Delivered or Cancelled, prevent any changes
    if curr_status in ("Delivered", "Cancelled"):
        conn.close()
        return {"success": False, "message": f"Order #{order_id} is already '{curr_status}' and cannot be modified again."}

    # 2. Prevent setting the same status again
    if curr_status == new_status:
        conn.close()
        return {"success": False, "message": f"Order #{order_id} is already in '{new_status}' status."}

    # 3. Enforce forward-only progression rules
    status_order = {
        "Preparing": 1,
        "Order Ready": 2,
        "Out for Delivery": 3,
        "Delivered": 4
    }

    if new_status != "Cancelled":
        curr_rank = status_order.get(curr_status, 1)
        new_rank = status_order.get(new_status, 1)
        if new_rank < curr_rank:
            conn.close()
            return {"success": False, "message": f"Cannot move order status backwards from '{curr_status}' to '{new_status}'."}

    cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
    conn.commit()
    conn.close()

    return {"success": True, "order_id": order_id, "status": new_status, "message": f"Order #{order_id} status updated from '{curr_status}' to '{new_status}'."}

def toggle_menu_availability(item_id, available=None, price=None):
    """
    Updates menu item availability (1 for in stock, 0 for out of stock) or price.
    """
    try:
        item_id = int(item_id)
    except (ValueError, TypeError):
        return {"success": False, "message": "item_id must be an integer"}

    conn = get_connection()
    cursor = conn.cursor()

    if available is not None:
        avail_val = 1 if available in (True, 1, "1", "true") else 0
        cursor.execute("UPDATE menu SET available = ? WHERE id = ?", (avail_val, item_id))

    if price is not None:
        try:
            p_val = float(price)
            cursor.execute("UPDATE menu SET price = ? WHERE id = ?", (p_val, item_id))
        except (ValueError, TypeError):
            pass

    conn.commit()
    conn.close()
    return {"success": True, "message": f"Menu item #{item_id} updated successfully."}

def add_menu_item(name, category, price, is_veg=1, description="", image_url=""):
    """
    Creates a new menu item in the database.
    """
    name_clean = (name or "").strip()
    cat_clean = (category or "").strip()
    if not name_clean or not cat_clean:
        return {"success": False, "message": "Item name and category are required."}

    try:
        p_val = float(price)
        veg_val = 1 if is_veg in (True, 1, "1", "true") else 0
    except (ValueError, TypeError):
        return {"success": False, "message": "Invalid price value."}

    img = (image_url or "").strip() or "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=500&q=80"
    desc = (description or "").strip() or f"Delicious {name_clean}"

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO menu (name, category, price, is_veg, description, rating, image_url, available)
           VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
        (name_clean, cat_clean, p_val, veg_val, desc, 4.5, img)
    )
    item_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {"success": True, "item_id": item_id, "message": f"Added '{name_clean}' to menu successfully."}

def delete_menu_item(item_id):
    """
    Deletes a menu item from the database.
    """
    try:
        item_id = int(item_id)
    except (ValueError, TypeError):
        return {"success": False, "message": "item_id must be an integer"}

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM menu WHERE id = ?", (item_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()

    if affected == 0:
        return {"success": False, "message": f"Item #{item_id} not found."}

    return {"success": True, "message": f"Deleted item #{item_id} from menu."}

def get_admin_analytics():
    """
    Calculates summary metrics for the restaurant dashboard: total revenue, order counts.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(total) FROM orders WHERE status != 'Cancelled'")
    total_revenue = cursor.fetchone()[0] or 0.0

    cursor.execute("SELECT COUNT(*) FROM orders WHERE status IN ('Preparing', 'Order Ready', 'Out for Delivery')")
    active_orders = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'Delivered'")
    delivered_orders = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'Cancelled'")
    cancelled_orders = cursor.fetchone()[0]

    conn.close()

    return {
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "active_orders": active_orders,
        "delivered_orders": delivered_orders,
        "cancelled_orders": cancelled_orders
    }

def clear_order_history():
    """
    Clears all order history from the database and resets autoincrement ID sequence.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orders")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='orders'")
    conn.commit()
    conn.close()

    return {"success": True, "message": "All order history has been cleared successfully."}

def get_restaurant_payment_details():
    """
    Retrieves Restaurant UPI and Bank details from the settings table.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()
    conn.close()

    settings = {r["key"]: r["value"] for r in rows}
    return {
        "success": True,
        "upi_id": settings.get("upi_id", "aahara@upi"),
        "merchant_name": settings.get("merchant_name", "Aahara Foods Pvt Ltd"),
        "bank_name": settings.get("bank_name", "HDFC Bank - Cyber City Branch"),
        "account_number": settings.get("account_number", "987654321098"),
        "ifsc_code": settings.get("ifsc_code", "HDFC0001234"),
        "qr_image_url": settings.get("qr_image_url", "https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=upi%3A%2F%2Fpay%3Fpa%3Daahara%40upi%26pn%3DAahara%2520Restaurant%26cu%3DINR")
    }

def update_restaurant_payment_details(upi_id=None, merchant_name=None, bank_name=None, account_number=None, ifsc_code=None, qr_image_url=None):
    """
    Updates Restaurant UPI and Bank details in the settings table.
    """
    conn = get_connection()
    cursor = conn.cursor()

    updates = {
        "upi_id": upi_id,
        "merchant_name": merchant_name,
        "bank_name": bank_name,
        "account_number": account_number,
        "ifsc_code": ifsc_code,
        "qr_image_url": qr_image_url
    }

    for key, val in updates.items():
        if val is not None and str(val).strip():
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(val).strip()))

    conn.commit()
    conn.close()
    return {"success": True, "message": "Restaurant UPI & Payment details updated successfully."}

def update_payment_status(order_id, payment_status):
    """
    Updates payment_status for an order (e.g. Paid (UPI), Paid (COD), Pending).
    """
    try:
        order_id = int(order_id)
    except (ValueError, TypeError):
        return {"success": False, "message": "order_id must be an integer"}

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET payment_status = ? WHERE id = ?", (payment_status, order_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()

    if affected == 0:
        return {"success": False, "message": f"Order #{order_id} not found."}

    return {"success": True, "order_id": order_id, "payment_status": payment_status, "message": f"Order #{order_id} payment status updated to '{payment_status}'."}
