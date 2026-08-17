# Aahara — AI-Powered Culinary & Food Ordering Assistant 🍽️🤖

**Aahara** is an intelligent, multi-provider AI Food Ordering web application built with **Flask**, **SQLite**, and **Modern Vanilla UI/CSS**. It allows users to interact with an AI Culinary Assistant to explore menus, filter vegetarian and budget-friendly dishes, manage cart items, apply promo codes, collect delivery details, and track live order progress.

---

## 🌟 Key Features

- **🤖 Intelligent Multi-LLM Agent**: Powered by **Groq** (`gpt-oss-120b`), **Google Gemini** (`gemini-3.5-flash`), or **OpenAI** (`gpt-4o-mini`) with seamless fallback.
- **🍽️ Interactive Visual Menu Gallery**: Dynamic category tabs (*Pizza, Burgers, Biryani, Sides, Drinks, Desserts*), Veg/Non-Veg badges (🌱/🍗), star ratings ⭐, descriptions, and 1-click **`+ Add`** buttons.
- **🛍️ Full Cart Controls**: Modify item quantities, remove items, or clear cart via AI chat or visual Cart Drawer.
- **🌱 Dietary & Budget Filters**: Search for dishes based on vegetarian preference (`is_veg`) or budget limits (`max_price`).
- **🎟️ Promo Codes & Discount Engine**: Apply discount codes like `AAHARA10` (10% OFF) or `WELCOME50` (₹50 OFF).
- **👤 Customer Details & Order Checkout**: Collect customer name, phone number, delivery address, and special cooking notes (*"extra spicy"*).
- **📦 Live Order Tracker & Receipts**: Track order status timeline (`Preparing 👨‍🍳` $\rightarrow$ `Out for Delivery 🛵` $\rightarrow$ `Delivered 🎉`).
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
Edit `.env`:
```env
GROQ_API_KEY=gsk_your_groq_key_here
GEMINI_API_KEY=your_gemini_key_here
```

### 4. Initialize Database & Run Server
```bash
python database.py
python app.py
```
Open **`http://127.0.0.1:5000`** in your browser.

---

## 🧪 Verification & Testing
Run the automated test suite to verify database schemas, cart tools, promo codes, and order tracking:
```bash
python verify_app.py
```

---

## 📜 License
MIT License. Built with ❤️ for food lovers and AI enthusiasts.
