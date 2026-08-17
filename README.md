# Aahara — AI-Powered Culinary & Food Ordering Assistant 🍽️🤖

**Aahara** is an intelligent, multi-provider AI Food Ordering web application built with **Flask**, **SQLite**, and **Modern Vanilla UI/CSS**. It features cleanly separated **Customer AI Assistant App** (`user/`) and **Restaurant Admin Web Portal** (`admin/`) modules that can be run independently or together.

---

## 📁 Repository Folder Structure

```text
Aahara/
├── user/                      <-- Customer App Module (user_bp)
│   ├── __init__.py
│   └── routes.py
├── admin/                     <-- Restaurant Admin Module (admin_bp)
│   ├── __init__.py
│   └── routes.py
├── templates/
│   ├── user/
│   │   └── index.html         <-- Customer App Template
│   └── admin/
│       ├── login.html         <-- Admin Login Template
│       └── dashboard.html     <-- Admin Live Dashboard Template
├── run_user.py                <-- Standalone Runner: Customer App (Port 5000)
├── run_admin.py               <-- Standalone Runner: Admin Portal (Port 5001)
├── app.py                     <-- Combined Runner: All Modules (Port 5000)
├── database.py                <-- Shared SQLite Database Engine
├── tools.py                   <-- Shared Tooling & Logic Engine
├── agent.py                   <-- Multi-LLM AI Agent Engine
└── verify_app.py              <-- 9-Step Automated Verification Suite
```

---

## 🌟 Key Features

- **🤖 Intelligent Multi-LLM Agent**: Powered by **Groq** (`gpt-oss-120b`), **Google Gemini** (`gemini-3.5-flash`), or **OpenAI** (`gpt-4o-mini`) with seamless fallback.
- **👨‍🍳 Restaurant Admin Web Portal**: Dedicated portal for kitchen staff to manage orders in real-time.
  - **Admin Credentials**: Email: `Admin@aahara.com` | Password: `Aahara@1939.`
  - **Live Order Board**: View incoming customer orders, customer details, payment status, and special cooking notes.
  - **Status Stepper Controls**: Update order status (`Preparing 👨‍🍳` $\rightarrow$ `Order Ready 🍽️` $\rightarrow$ `Out for Delivery 🛵` $\rightarrow$ `Delivered 🎉` / `Cancelled ❌`).
  - **One-Way Locking**: Status locks upon progression to prevent backward changes.
  - **UPI QR Code & Bank Manager**: Manage Restaurant UPI ID, Bank details, and QR Code URL with live preview.
  - **KOT Slip Printing**: 1-click printable receipt slip (`window.print()`).
  - **Real-Time Order Search**: Filter orders by ID, Customer Name, or Phone number.
  - **Clear Orders**: 1-click order history reset option.
- **💳 Payment Integration (Simulation Model)**:
  - **📱 UPI Payment**: Renders Restaurant UPI QR Code, UPI ID (`aahara@upi`), Bank info, and UTR input.
  - **💵 Cash on Delivery (COD)**: Confirms order with Cash on Delivery payment status.
- **🍽️ Interactive Visual Menu Gallery**: Category tabs (*Pizza, Burgers, Biryani, Sides, Drinks, Desserts*), Veg/Non-Veg badges (🌱/🍗), ratings ⭐, descriptions, and 1-click **`+ Add`** buttons.
- **🛍️ Full Cart Controls**: Modify item quantities, remove items, or clear cart via AI chat or visual Cart Drawer.
- **🌱 Dietary & Budget Filters**: Search for dishes based on vegetarian preference (`is_veg`) or budget limits (`max_price`).
- **🎟️ Promo Codes & Discount Engine**: Apply discount codes like `AAHARA10` (10% OFF) or `WELCOME50` (₹50 OFF).
- **👤 Customer Details & Order Checkout**: Collect customer name, phone number, delivery address, and special cooking notes (*"extra spicy"*).
- **🎙️ Voice Dictation**: Speech-to-text input via browser Web Speech API.

---

## 🏗️ Tech Stack

- **Frontend**: HTML5, Modern CSS3 (Variables, Glassmorphism, Micro-animations), JavaScript ES6+
- **Backend**: Python 3.12, Flask, SQLite3
- **AI Agent & LLM APIs**: OpenAI Python SDK, Groq API, Google Gemini OpenAI-compatible REST API

---

## 🚀 Quick Start Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/Yallanti1939/AAHARA.git
cd AAHARA
```

### 2. Set Up Virtual Environment & Dependencies
```bash
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

pip install flask python-dotenv openai
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your API key(s):
```bash
cp .env.example .env
```

### 4. Running the Portals

#### Option A: Run Apps Independently (Separate Servers)
- **Customer App (Port 5000)**:
  ```bash
  python run_user.py
  ```
  Open **`http://127.0.0.1:5000`**

- **Restaurant Admin Portal (Port 5001)**:
  ```bash
  python run_admin.py
  ```
  Open **`http://127.0.0.1:5001/admin`**

#### Option B: Run Combined Platform
```bash
python app.py
```
- **Customer App**: **`http://127.0.0.1:5000`**
- **Admin Portal**: **`http://127.0.0.1:5000/admin`**

- **Admin Login Email**: `Admin@aahara.com`
- **Admin Login Password**: `Aahara@1939.`

---

## 🧪 Verification & Testing
Run the 9-step automated test suite:
```bash
python verify_app.py
```

---

## 📜 License
MIT License. Built with ❤️ for food lovers and AI enthusiasts.
