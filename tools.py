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
    sql = f"SELECT id, name, category, price, is_veg, description, rating, image_url FROM menu WHERE {where_clause} ORDER BY category, name"
    
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    
    results = [dict(row) for row in rows]
    if not results:
        filter_str = f"'{query}'" if query else "specified criteria"
        return {"found": False, "message": f"No menu items found matching {filter_str}."}
    
    return {"found": True, "count": len(results), "items": results}

def get_full_menu():
    return search_menu("all")

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

def place_order(customer_name="", customer_phone="", delivery_address="", notes="", promo_code=None):
    """
    Places order with full customer details (customer_name, customer_phone, delivery_address), cart items, notes, and saves to database.
    """
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

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO orders (items, subtotal, discount, total, status, customer_name, customer_phone, delivery_address, notes, promo_code, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (items_json, subtotal, discount, total, "Preparing", c_name, c_phone, c_addr, notes or "", applied_code, created_str)
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
        "notes": notes,
        "message": f"Order #{order_id} placed for {c_name}! Delivery to '{c_addr}'. Total: ₹{total:.2f}. Status: Preparing."
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
        "notes": order["notes"] if "notes" in order.keys() else "",
        "created_at": order["created_at"] if "created_at" in order.keys() else "",
        "items": json.loads(order["items"])
    }

def get_order_history():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 5")
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for r in rows:
        history.append({
            "order_id": r["id"],
            "customer_name": r["customer_name"] if "customer_name" in r.keys() else "Customer",
            "customer_phone": r["customer_phone"] if "customer_phone" in r.keys() else "",
            "delivery_address": r["delivery_address"] if "delivery_address" in r.keys() else "",
            "total": r["total"],
            "status": r["status"],
            "created_at": r["created_at"] if "created_at" in r.keys() else "",
            "items": json.loads(r["items"])
        })
        
    return {"count": len(history), "orders": history}
