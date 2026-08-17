# Aahara — AI-Powered Culinary & Food Ordering Assistant 🍽️🤖

**Aahara** is an intelligent, multi-provider AI Food Ordering web application built with **Flask**, **SQLite**, and **Modern Vanilla UI/CSS**. It features **Two Independent, Interconnected Portals** running on separate servers for **Customers** and **Restaurant Admins**.

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
├── run_servers.py             <-- ⚡ Master Parallel Launcher (Dual-Server Mode)
├── run_user.py                <-- Standalone Server: Customer App (Port 5000)
├── run_admin.py               <-- Standalone Server: Admin Portal (Port 5001)
├── app.py                     <-- Combined Server: All Modules (Port 5000)
├── database.py                <-- Shared SQLite Database Engine
├── tools.py                   <-- Shared Tooling & Logic Engine
├── agent.py                   <-- Multi-LLM AI Agent Engine
└── verify_app.py              <-- 9-Step Automated Verification Suite
```

---

## 🌐 Dual-Server Interconnected Architecture

| Portal | Port & URL | Function | Cross-Navigation |
| :--- | :--- | :--- | :--- |
| **🚀 Customer AI App** | `http://127.0.0.1:5000` | AI Menu Search, Voice Order, Cart, UPI QR / COD Checkout & Stepper Tracker | Link to Admin Portal (`:5001/admin`) |
| **👨‍🍳 Restaurant Admin** | `http://127.0.0.1:5001/admin` | Live Kitchen Orders Board, One-Way Status Stepper, UPI QR Manager & KOT Slip Print | Link to Customer App (`:5000`) |

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

### 4. Run Both Servers Concurrently (Recommended)

Run the master dual-server orchestrator script:
```bash
python run_servers.py
```

- **🚀 Customer App Server**: **`http://127.0.0.1:5000`**
- **👨‍🍳 Restaurant Admin Server**: **`http://127.0.0.1:5001/admin`**
  - **Login Email**: `Admin@aahara.com`
  - **Login Password**: `Aahara@1939.`

---

## 🧪 Verification & Testing
Run the 9-step automated test suite:
```bash
python verify_app.py
```

---

## 📜 License
MIT License. Built with ❤️ for food lovers and AI enthusiasts.
