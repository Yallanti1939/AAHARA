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

    # --------------------------------------------------
    # Test 6: Sequential Status Progression & One-Way Locking
    # --------------------------------------------------
    print("\n[TEST 6] Testing Sequential Status Progression (Preparing -> Order Ready -> Out for Delivery -> Delivered -> Locked)...")
    
    # 1. Add item to cart and place a fresh order
    tools.add_to_cart(test_id, 1)
    new_order = tools.place_order(customer_name="Admin Sync Test", delivery_address="Kitchen Test Bench")
    order_id = new_order["order_id"]
    print(f"Created Test Order #{order_id}, initial status={new_order['status']}")

    # 2. Advance to 'Order Ready'
    up1 = tools.update_order_status(order_id, "Order Ready")
    print(f"Status Step 1 (Order Ready): {up1.get('message')}")
    if not up1.get("success") or tools.track_order(order_id)["status"] != "Order Ready":
        print("FAIL: Could not update to 'Order Ready'.")
        return False

    # 3. Advance to 'Out for Delivery'
    up2 = tools.update_order_status(order_id, "Out for Delivery")
    print(f"Status Step 2 (Out for Delivery): {up2.get('message')}")
    if not up2.get("success") or tools.track_order(order_id)["status"] != "Out for Delivery":
        print("FAIL: Could not update to 'Out for Delivery'.")
        return False

    # 4. Advance to 'Delivered'
    up3 = tools.update_order_status(order_id, "Delivered")
    print(f"Status Step 3 (Delivered): {up3.get('message')}")
    if not up3.get("success") or tools.track_order(order_id)["status"] != "Delivered":
        print("FAIL: Could not update to 'Delivered'.")
        return False

    # 5. Verify locking rule: Attempting to modify status after Delivered MUST FAIL!
    up_locked = tools.update_order_status(order_id, "Preparing")
    print(f"Lock Rule Check (Attempt backward change): {up_locked.get('message')}")
    if up_locked.get("success"):
        print("FAIL: Locking rule violated! Status was allowed to change after Delivered.")
        return False

    print("PASS: Sequential progression and status locking verified successfully.")

    # --------------------------------------------------
    # Test 7: Admin Menu Management (Add & Delete Dish)
    # --------------------------------------------------
    print("\n[TEST 7] Testing Admin Menu Management (Add & Delete Dish)...")
    add_res = tools.add_menu_item("Chef's Special Special Biryani", "Biryani", 349.0, 0, "Aromatic spice infused biryani", "")
    print(f"Add Dish Result: {add_res.get('message')}")
    if not add_res.get("success"):
        print("FAIL: Could not add menu item.")
        return False

    new_item_id = add_res["item_id"]
    del_res = tools.delete_menu_item(new_item_id)
    print(f"Delete Dish Result: {del_res.get('message')}")
    if not del_res.get("success"):
        print("FAIL: Could not delete menu item.")
        return False

    print("PASS: Admin menu management (add & delete) verified successfully.")

    # --------------------------------------------------
    # Test 8: Clear Order History
    # --------------------------------------------------
    print("\n[TEST 8] Testing Clear Orders Functionality...")
    clear_res = tools.clear_order_history()
    print(f"Clear Orders Result: {clear_res.get('message')}")
    if not clear_res.get("success"):
        print("FAIL: Could not clear order history.")
        return False

    history_after = tools.get_order_history()
    if history_after["count"] != 0:
        print(f"FAIL: Expected 0 orders after clear, got {history_after['count']}.")
        return False

    print("PASS: Clear orders history functionality verified successfully.")

    # --------------------------------------------------
    # Test 9: Payment Integration (UPI & COD) & Settings
    # --------------------------------------------------
    print("\n[TEST 9] Testing Payment Integration (UPI QR, COD & Settings)...")
    tools.add_to_cart(test_id, 1)
    upi_order = tools.place_order(
        customer_name="UPI Tester",
        delivery_address="Digital City",
        payment_method="UPI",
        transaction_id="UTR9876543210"
    )
    print(f"UPI Order Result: {upi_order.get('message')}")
    if upi_order.get("payment_method") != "UPI" or upi_order.get("payment_status") != "Paid (UPI)":
        print("FAIL: UPI payment method/status mismatch.")
        return False

    tools.add_to_cart(test_id, 1)
    cod_order = tools.place_order(
        customer_name="COD Tester",
        delivery_address="Cash Lane",
        payment_method="Cash on Delivery"
    )
    print(f"COD Order Result: {cod_order.get('message')}")
    if cod_order.get("payment_method") != "Cash on Delivery":
        print("FAIL: COD payment method mismatch.")
        return False

    pay_status_up = tools.update_payment_status(cod_order["order_id"], "Paid (COD)")
    print(f"Admin Payment Status Update: {pay_status_up.get('message')}")

    set_up = tools.update_restaurant_payment_details(upi_id="admin@aahara", merchant_name="Aahara Kitchen")
    print(f"Payment Details Update: {set_up.get('message')}")

    pay_details = tools.get_restaurant_payment_details()
    if pay_details.get("upi_id") != "admin@aahara":
        print(f"FAIL: Updated UPI ID expected 'admin@aahara', got '{pay_details.get('upi_id')}'.")
        return False

    # Clean up test orders after verification
    tools.clear_order_history()
    print("PASS: Payment integration (UPI, COD & Settings) verified successfully.")

    print("\n==================================================")
    print("ALL ENHANCED TESTS PASSED! Aahara is world-class.")
    print("==================================================")
    return True

if __name__ == "__main__":
    run_tests()
