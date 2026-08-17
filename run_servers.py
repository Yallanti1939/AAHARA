import threading
import time
from database import init_db
from run_user import app as user_app
from run_admin import app as admin_app

# Initialize database
init_db()

def run_customer_server():
    print("🌐 Customer Server starting on http://127.0.0.1:5000...")
    user_app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

def run_admin_server():
    print("👨‍🍳 Restaurant Admin Server starting on http://127.0.0.1:5001/admin...")
    admin_app.run(host="127.0.0.1", port=5001, debug=False, use_reloader=False)

if __name__ == "__main__":
    print("=" * 65)
    print("🚀 Starting Aahara Dual-Server Architecture (2 Independent Servers)...")
    print("🌐 Server 1 (Customer App):          http://127.0.0.1:5000")
    print("👨‍🍳 Server 2 (Restaurant Admin):      http://127.0.0.1:5001/admin")
    print("=" * 65)

    t1 = threading.Thread(target=run_customer_server, daemon=True)
    t2 = threading.Thread(target=run_admin_server, daemon=True)

    t1.start()
    t2.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Aahara Servers.")
