from flask import render_template, request, jsonify, session
from . import user_bp
from agent import run_agent
from tools import (
    view_cart, get_full_menu, add_to_cart, remove_from_cart,
    update_cart_quantity, clear_cart, apply_promo_code,
    get_order_history, track_order, get_restaurant_payment_details
)

@user_bp.route("/")
def home():
    if "chat_history" not in session:
        session["chat_history"] = []
    return render_template("index.html")

@user_bp.route("/chat", methods=["POST"])
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

@user_bp.route("/cart", methods=["GET"])
def get_cart():
    cart_info = view_cart()
    return jsonify(cart_info)

@user_bp.route("/api/menu", methods=["GET"])
def api_menu():
    menu_data = get_full_menu()
    return jsonify(menu_data)

@user_bp.route("/api/cart/modify", methods=["POST"])
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

@user_bp.route("/api/orders", methods=["GET"])
def api_orders():
    order_id = request.args.get("order_id")
    if order_id:
        return jsonify(track_order(order_id))
    return jsonify(get_order_history())

@user_bp.route("/api/payment-details", methods=["GET"])
def api_payment_details():
    return jsonify(get_restaurant_payment_details())

@user_bp.route("/clear_chat", methods=["POST"])
def clear_chat():
    session["chat_history"] = []
    return jsonify({"success": True, "message": "Chat history cleared."})
