import os
from flask import Flask, redirect, url_for
from database import init_db
from admin import admin_bp

# Initialize database
init_db()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "aahara_culinary_secret_key_9876")

# Register Restaurant Admin Blueprint
app.register_blueprint(admin_bp, url_prefix="/admin")

@app.route("/")
def index():
    return redirect(url_for("admin.admin_login"))

if __name__ == "__main__":
    print("=" * 60)
    print("👨‍🍳 Starting Aahara Restaurant Admin Portal Independently...")
    print("🌐 Access Admin Portal at: http://127.0.0.1:5001/admin")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5001, debug=True)
