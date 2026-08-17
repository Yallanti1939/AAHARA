import os
from flask import Flask
from database import init_db
from user import user_bp
from admin import admin_bp

# Initialize database on startup
init_db()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "aahara_culinary_secret_key_9876")

# Register Blueprints for Customer and Admin Apps
app.register_blueprint(user_bp)
app.register_blueprint(admin_bp, url_prefix="/admin")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting Combined Aahara Platform (Customer App & Admin Portal)...")
    print("🌐 Customer App: http://127.0.0.1:5000")
    print("👨‍🍳 Admin Portal: http://127.0.0.1:5000/admin")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5000, debug=True)
