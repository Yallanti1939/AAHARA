import os
from flask import render_template, request, jsonify, session, redirect, url_for
from . import admin_bp
from tools import (
    get_order_history, update_order_status,
    get_full_menu, toggle_menu_availability, add_menu_item,
    delete_menu_item, clear_order_history, get_admin_analytics,
    get_restaurant_payment_details, update_restaurant_payment_details,
    update_payment_status
)

ADMIN_EMAIL = "admin@aahara.com"
ADMIN_PASSWORD = "Aahara@1939."

@admin_bp.route("/")
@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin.admin_dashboard"))

    error = None
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = (request.form.get("password") or "").strip()

        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            session["admin_email"] = ADMIN_EMAIL
            return redirect(url_for("admin.admin_dashboard"))
        else:
            error = "Invalid Admin Credentials. Please check your email and password."

    return render_template("login.html", error=error)

@admin_bp.route("/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_email", None)
    return redirect(url_for("admin.admin_login"))

@admin_bp.route("/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin.admin_login"))
    return render_template("dashboard.html")

@admin_bp.route("/api/orders", methods=["GET"])
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

@admin_bp.route("/api/order/status", methods=["POST"])
def api_admin_update_status():
    if not session.get("admin_logged_in"):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    order_id = data.get("order_id")
    status = data.get("status")

    res = update_order_status(order_id, status)
    return jsonify(res)

@admin_bp.route("/api/order/payment-status", methods=["POST"])
def api_admin_update_payment_status():
    if not session.get("admin_logged_in"):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    order_id = data.get("order_id")
    payment_status = data.get("payment_status")

    res = update_payment_status(order_id, payment_status)
    return jsonify(res)

@admin_bp.route("/api/menu", methods=["GET"])
def api_admin_full_menu():
    if not session.get("admin_logged_in"):
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    return jsonify(get_full_menu(include_unavailable=True))

@admin_bp.route("/api/menu/toggle", methods=["POST"])
def api_admin_toggle_menu():
    if not session.get("admin_logged_in"):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    item_id = data.get("item_id")
    available = data.get("available")
    price = data.get("price")

    res = toggle_menu_availability(item_id, available, price)
    return jsonify(res)

@admin_bp.route("/api/menu/add", methods=["POST"])
def api_admin_add_menu():
    if not session.get("admin_logged_in"):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    name = data.get("name")
    category = data.get("category")
    price = data.get("price")
    is_veg = data.get("is_veg", 1)
    description = data.get("description", "")
    image_url = data.get("image_url", "")

    res = add_menu_item(name, category, price, is_veg, description, image_url)
    return jsonify(res)

@admin_bp.route("/api/menu/delete", methods=["POST"])
def api_admin_delete_menu():
    if not session.get("admin_logged_in"):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    item_id = data.get("item_id")

    res = delete_menu_item(item_id)
    return jsonify(res)

@admin_bp.route("/api/orders/clear", methods=["POST"])
def api_admin_clear_orders():
    if not session.get("admin_logged_in"):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    res = clear_order_history()
    return jsonify(res)

@admin_bp.route("/api/payment-settings", methods=["GET", "POST"])
def api_admin_payment_settings():
    if request.method == "POST":
        if not session.get("admin_logged_in"):
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        data = request.get_json() or {}
        upi_id = data.get("upi_id")
        merchant_name = data.get("merchant_name")
        bank_name = data.get("bank_name")
        account_number = data.get("account_number")
        ifsc_code = data.get("ifsc_code")
        qr_image_url = data.get("qr_image_url")

        res = update_restaurant_payment_details(upi_id, merchant_name, bank_name, account_number, ifsc_code, qr_image_url)
        return jsonify(res)

    # GET request available publicly so customer app can load payment details too
    return jsonify(get_restaurant_payment_details())
