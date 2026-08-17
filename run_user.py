import os
from flask import Flask
from database import init_db
from user import user_bp

# Initialize database
init_db()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "aahara_culinary_secret_key_9876")

# Register Customer Blueprint
app.register_blueprint(user_bp)

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting Aahara Customer AI App Independently...")
    print("🌐 Access App at: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5000, debug=True)
