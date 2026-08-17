import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from database import init_db
from agent import run_agent
from tools import (
    view_cart, get_full_menu, add_to_cart, remove_from_cart,
    update_cart_quantity, clear_cart, apply_promo_code,
    get_order_history, track_order, update_order_status,
    toggle_menu_availability, get_admin_analytics
)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "aahara_culinary_secret_key_9876")

# Hardcoded Restaurant Admin Credentials as requested
ADMIN_EMAIL = "admin@aahara.com"
ADMIN_PASSWORD = "Aahara@1939."

# Initialize database on startup
init_db()

# --------------------------------------------------
# CUSTOMER FACING ROUTES
# --------------------------------------------------

@app.route("/")
def home():
    if "chat_history" not in session:
        session["chat_history"] = []
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    user_message = data.get("message", "")
    
    if not user_message.strip():
        return jsonify({"response": "Please type a message."})
        
    history = session.get("chat_history", [])
    
    try:
        response, updated_history = run_agent(user_message, history)
        session["chat_history"] = updated_history
        return jsonify({"response": response})
    except Exception as e:
        print(f"[ERROR] {e}")
        error_msg = str(e)
        if "insufficient_quota" in error_msg or "credit_balance_exhausted" in error_msg or "429" in error_msg:
            return jsonify({"response": "API quota or credit balance exhausted. Please check your API account settings or update your .env file."})
        if "APIKey" in error_msg or "api_key" in error_msg or "API_KEY" in error_msg:
            return jsonify({"response": "API Key is missing or invalid. Please check your .env configuration."})
        return jsonify({"response": f"Sorry, something went wrong while processing your request: {error_msg}"})

@app.route("/cart", methods=["GET"])
def get_cart():
    cart_info = view_cart()
    return jsonify(cart_info)

@app.route("/api/menu", methods=["GET"])
def api_menu():
    menu_data = get_full_menu()
    return jsonify(menu_data)

@app.route("/api/cart/modify", methods=["POST"])
def modify_cart():
    data = request.get_json() or {}
    action = data.get("action")
    item_id = data.get("item_id")
    quantity = data.get("quantity")
    code = data.get("code")

    if action == "add":
        result = add_to_cart(item_id, quantity or 1)
    elif action == "remove":
        result = remove_from_cart(item_id, quantity)
    elif action == "update":
        result = update_cart_quantity(item_id, quantity)
    elif action == "clear":
        result = clear_cart()
    elif action == "promo":
        result = apply_promo_code(code)
    else:
        return jsonify({"success": False, "message": "Unknown action"}), 400

    cart_state = view_cart()
    result["cart_state"] = cart_state
    return jsonify(result)

@app.route("/api/orders", methods=["GET"])
def api_orders():
    order_id = request.args.get("order_id")
    if order_id:
        return jsonify(track_order(order_id))
    return jsonify(get_order_history())

@app.route("/clear_chat", methods=["POST"])
def clear_chat():
    session["chat_history"] = []
    return jsonify({"success": True, "message": "Chat history cleared."})

# --------------------------------------------------
# RESTAURANT ADMIN PORTAL ROUTES
# --------------------------------------------------

@app.route("/admin")
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))

    error = None
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = (request.form.get("password") or "").strip()

        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            session["admin_email"] = ADMIN_EMAIL
            return redirect(url_for("admin_dashboard"))
        else:
            error = "Invalid Admin Credentials. Please check your email and password."

    return render_template("admin_login.html", error=error)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_email", None)
    return redirect(url_for("admin_login"))

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    return render_template("admin_dashboard.html")

@app.route("/api/admin/orders", methods=["GET"])
def api_admin_orders():
    if not session.get("admin_logged_in"):
        return jsonify({"success": False, "message": "Unauthorized"}), 401
        
    orders_data = get_order_history()
    analytics = get_admin_analytics()
    return jsonify({
        "success": True,
        "analytics": analytics,
        "orders": orders_data.get("orders", [])
    })

@app.route("/api/admin/order/status", methods=["POST"])
def api_admin_update_status():
    if not session.get("admin_logged_in"):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    order_id = data.get("order_id")
    status = data.get("status")

    res = update_order_status(order_id, status)
    return jsonify(res)

@app.route("/api/admin/menu", methods=["GET"])
def api_admin_full_menu():
    if not session.get("admin_logged_in"):
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    return jsonify(get_full_menu(include_unavailable=True))

@app.route("/api/admin/menu/toggle", methods=["POST"])
def api_admin_toggle_menu():
    if not session.get("admin_logged_in"):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    item_id = data.get("item_id")
    available = data.get("available")
    price = data.get("price")

    res = toggle_menu_availability(item_id, available, price)
    return jsonify(res)

if __name__ == "__main__":
    app.run(debug=True)
