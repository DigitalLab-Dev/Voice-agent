# 📘 Digital Lab AI Calling Agent - Complete Technical Documentation

**Version:** 2.0 (Final Release)  
**Date:** December 2025  
**Engine:** Groq (Llama 3.3)  

---

## 📋 1. Project Overview

The **Digital Lab AI Calling Agent** is a full-stack platform that allows businesses to create AI-powered voice agents. These agents can conduct voice conversations with customers, answer questions based on a customizable prompt, and collect leads.

### **Core Capabilities**
- **Multi-Tenant System**: Users can sign up, log in, and manage their own agents.
- **Custom AI Agents**: Users can build agents with unique names, system prompts, voices, and greeting messages.
- **Real-Time Voice AI**: Uses Web Speech API (STT/TTS) + Groq Llama 3 (LLM) for sub-second conversational latency.
- **Analytics & Leads**: Tracks call duration, message count, and automatically detects "Leads" based on conversation sentiment.
- **Admin Dashboard**: A super-admin view to monitor system-wide usage.

---

## 🏗️ 2. System Architecture

```mermaid
graph TD
    User[End User] -->|HTTPS| Frontend[Frontend (Flask Templates + JS)]
    Frontend -->|REST API| Backend[Flask Backend (app.py)]
    Frontend -->|Web Speech API| Browser[Browser STT/TTS]
    
    subgraph "Backend Services"
        Backend -->|Auth| AuthMgr[Auth Manager (auth.py)]
        Backend -->|AI Logic| AISvc[AI Services (ai_services.py)]
        Backend -->|Data| DB[Database Manager (database.py)]
    end
    
    subgraph "External APIs"
        AISvc -->|Inference| Groq[Groq API (Llama 3)]
    end
    
    subgraph "Storage"
        DB -->|SQL| SQLite[(conversations.db)]
    end
```

---

## 💾 3. Database Schema (SQLite)

The system uses a relational SQLite database (`conversations.db`) with 4 main tables:

### **1. Users (`users`)**
Stores platform accounts.
- `id`: PK
- `email`: User email (Unique)
- `password_hash`: Securely hashed password
- `full_name`: User's name

### **2. Agents (`agents`)**
Stores custom AI personas created by users.
- `id`: PK
- `user_id`: FK -> users.id (Ownership)
- `business_name`: Name of the agent
- `system_prompt`: The "brain" of the agent (instructions)
- `greeting_message`: First sentence spoken
- `voice_id`: TTS voice setting

### **3. Conversations (`conversations`)**
Stores call metadata.
- `id`: PK
- `agent_id`: FK -> agents.id (Links call to specific agent)
- `timestamp`: Start time
- `duration`: Length in seconds
- `message_count`: Total exchanges
- `sentiment`: 'Positive', 'Neutral', 'Negative' (AI analyzed)
- `summary`: Text summary of the call

### **4. Messages (`messages`)**
Stores the actual chat transcript.
- `id`: PK
- `conversation_id`: FK -> conversations.id
- `role`: 'user' (Customer) or 'agent' (AI)
- `content`: Text of the message

---

## 🧠 4. Key Features & Logic

### **A. Authentication & Security**
- **JWT (JSON Web Tokens)**: Used for stateless authentication.
- **Flow**:
  1. User enters Email/Pass -> `/api/auth/login`.
  2. Backend verifies hash -> Returns `access_token`.
  3. Frontend stores token in `localStorage`.
  4. All subsequent API calls include `Authorization: Bearer <token>`.
- **Protection**: Routes like `/dashboard` and `/api/my-agents` are protected.

### **B. The "Lead Generation" Logic**
A unique feature is how the system defines a "Lead".
- **Old Logic**: Counted every message as a lead (Inaccurate).
- **New Logic**: A **Lead** is defined as a conversation where the **Sentiment is Positive**.
- **Process**:
  1. Call Ends.
  2. User clicks "Generate Summary".
  3. AI analyzes transcript -> Assigns Sentiment (Positive/Neutral/Negative).
  4. If `Sentiment == 'Positive'`, the "Leads Generated" counter increments.

### **C. AI Service (Groq Integration)**
- **Engine**: Groq API running `llama-3.3-70b-versatile`.
- **Reason**: Chosen for extreme speed (low latency) which is critical for voice.
- **Context Management**: Keeps the last 10 messages in memory to maintain conversational context without exceeding token limits.

### **D. Data Isolation**
- **Result**: User A cannot see User B's agents or calls.
- **Implementation**: All SQL queries filter by `user_id`.
  - `get_user_agents(user_id)`
  - `get_statistics(agent_id)`: Verifies `agent.user_id == current_user.id`.

---

## 🔌 5. API Reference

### **Authentication**
- `POST /api/auth/signup`: Create account.
- `POST /api/auth/login`: Get JWT token.

### **Agents**
- `POST /api/agent/create`: Build a new AI agent.
- `GET /api/agent/list`: Get all agents for logged-in user.

### **Calls**
- `POST /api/start_call`: Initialize session (creates `conversation` record).
- `POST /api/send_message`: Send text -> Get AI Audio/Text response.
- `POST /api/end_call`: Finalize duration and save messages.

### **Data & Stats**
- `GET /api/conversations`: Get history (filtered by Agent).
- `GET /api/statistics`: Get dashboard metrics (Calls, Duration, Leads).
- `POST /api/generate_summary`: Trigger AI summary & sentiment analysis.

### **Admin**
- `GET /api/admin/stats`: System-wide totals.
- `GET /api/admin/users`: List of all registered users.

---

## 🖥️ 6. Frontend Structure

1. **`landing.html`**: Marketing page.
2. **`login.html` / `signup.html`**: Auth pages.
3. **`dashboard.html`**: Main Hub. Shows stats and "Launch Agent" button.
4. **`agent_builder.html`**: Form to create new agents.
5. **`index.html` (The Calling Interface)**:
   - The actual "Phone" UI.
   - Handles Microphone access.
   - Displays real-time transcript.
6. **`admin.html`**: Hidden super-admin panel (`/admin`).

---

## 🚀 7. How to Run

### **Prerequisites**
- Python 3.8+
- Groq API Key (Set in `ai_services.py`)

### **Installation**
```bash
# 1. Create Virtual Environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install Dependencies
pip install -r requirements.txt
```

### **Running**
```bash
python app.py
```
- **App**: `http://localhost:5001`
- **Admin**: `http://localhost:5001/admin`

---

## 🛡️ 8. Admin Credentials
To access the Admin Panel, you must log in with:
- **Email**: `admin@digitallab.com`
- **Password**: (Any password you set during signup for this email)
- *Note: This email is hardcoded in the backend as the "Super User".*
