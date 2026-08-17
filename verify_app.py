import os
import json
import sqlite3
from database import init_db, DB_NAME, get_connection
import tools

def run_tests():
    print("==================================================")
    print("Starting Aahara Enhanced Verification Suite")
    print("==================================================")
    
    # --------------------------------------------------
    # Test 1: Database Initialization & Schema
    # --------------------------------------------------
    print("\n[TEST 1] Initializing Database & Verifying Schema...")
    init_db()
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables found: {tables}")
    if "menu" not in tables or "orders" not in tables:
        print("FAIL: menu or orders table is missing.")
        conn.close()
        return False
        
    cursor.execute("SELECT COUNT(*) FROM menu")
    menu_count = cursor.fetchone()[0]
    print(f"Seeded menu items count: {menu_count}")
    if menu_count < 10:
        print(f"FAIL: Expected at least 10 menu items, got {menu_count}.")
        conn.close()
        return False
        
    conn.close()
    print("PASS: Database initialized and seeded successfully.")
    
    # --------------------------------------------------
    # Test 2: Search Menu & Filters (is_veg & max_price)
    # --------------------------------------------------
    print("\n[TEST 2] Testing search_menu() & Dietary Filters...")
    
    # Search for veg items only
    veg_res = tools.search_menu(is_veg=True)
    print(f"Veg search count: {veg_res.get('count')}")
    if not veg_res.get("found") or any(i["is_veg"] != 1 for i in veg_res["items"]):
        print("FAIL: Veg filter returned non-veg items.")
        return False
        
    # Search for items under ₹200
    cheap_res = tools.search_menu(max_price=200.0)
    print(f"Items under ₹200 count: {cheap_res.get('count')}")
    if not cheap_res.get("found") or any(i["price"] > 200.0 for i in cheap_res["items"]):
        print("FAIL: Price filter returned items over max_price.")
        return False

    print("PASS: search_menu() dietary & budget filters are accurate.")

    # --------------------------------------------------
    # Test 3: Full Cart Controls (Add, Modify, Remove, Clear)
    # --------------------------------------------------
    print("\n[TEST 3] Testing Cart Controls (Add, Remove, Update, Clear)...")
    tools.clear_cart()
    test_item = cheap_res['items'][0]
    test_id = test_item['id']
    
    # Add item x 2
    add_res1 = tools.add_to_cart(test_id, 2)
    print(f"Add item {test_id} x 2: {add_res1.get('message')}")
    if not add_res1.get("success") or len(tools.cart) != 1:
        print("FAIL: Could not add item to cart.")
        return False

    # Update qty to 3
    up_res = tools.update_cart_quantity(test_id, 3)
    print(f"Update item {test_id} qty to 3: {up_res.get('message')}")
    if tools.cart[0]["quantity"] != 3:
        print("FAIL: Quantity not updated to 3.")
        return False

    # Remove 1 item
    rem_res = tools.remove_from_cart(test_id, 1)
    print(f"Remove 1 qty: {rem_res.get('message')}")
    if tools.cart[0]["quantity"] != 2:
        print("FAIL: Quantity not reduced to 2.")
        return False

    print("PASS: Cart controls function correctly.")

    # --------------------------------------------------
    # Test 4: Promo Code & Discount Calculations
    # --------------------------------------------------
    print("\n[TEST 4] Testing Promo Codes (AAHARA10 & WELCOME50)...")
    
    # Apply AAHARA10 (10% OFF)
    promo_res = tools.apply_promo_code("AAHARA10")
    print(f"Apply AAHARA10: {promo_res.get('message')}")
    cart_calc = tools.view_cart()
    expected_subtotal = tools.cart[0]["price"] * tools.cart[0]["quantity"] # 199 * 2 = 398
    expected_discount = round(expected_subtotal * 0.10, 2) # 39.80
    print(f"Subtotal: {cart_calc['subtotal']}, Discount: {cart_calc['discount']}, Total: {cart_calc['total']}")
    if cart_calc["discount"] != expected_discount:
        print(f"FAIL: Expected discount {expected_discount}, got {cart_calc['discount']}.")
        return False

    print("PASS: Promo code engine and discount calculations are accurate.")

    # --------------------------------------------------
    # Test 5: Place Order with Customer Details & Notes
    # --------------------------------------------------
    print("\n[TEST 5] Testing place_order() with Customer Details (Name, Phone, Address)...")
    
    order_res = tools.place_order(
        customer_name="Rahul Sharma",
        customer_phone="9876543210",
        delivery_address="Flat 402, Sunshine Apts, MG Road",
        notes="Extra spicy, no pickles",
        promo_code="AAHARA10"
    )
    print(f"Place Order Output: order_id={order_res.get('order_id')}, customer={order_res.get('customer_name')}, total={order_res.get('total')}")
    if not order_res.get("success") or order_res.get("customer_name") != "Rahul Sharma":
        print("FAIL: Could not place order with customer details.")
        return False

    # Verify order tracking
    track_res = tools.track_order(order_res["order_id"])
    print(f"Track Order Output: customer_name={track_res.get('customer_name')}, phone={track_res.get('customer_phone')}, address={track_res.get('delivery_address')}")
    if not track_res.get("found") or track_res.get("delivery_address") != "Flat 402, Sunshine Apts, MG Road":
        print("FAIL: Track order missing customer address or invalid status.")
        return False

    # Verify order history
    hist_res = tools.get_order_history()
    print(f"Order History Count: {hist_res.get('count')}")
    if hist_res.get("count") < 1:
        print("FAIL: Order history is empty.")
        return False

    print("PASS: Place order, order tracking, and history with customer details succeed.")

    print("\n==================================================")
    print("ALL ENHANCED TESTS PASSED! Aahara is world-class.")
    print("==================================================")
    return True

if __name__ == "__main__":
    run_tests()
