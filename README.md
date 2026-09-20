# 🤖 Full-Stack AI RAG Chatbot

An enterprise-ready, lightweight, and beginner-friendly **Retrieval-Augmented Generation (RAG) Chatbot Application** featuring **User Authentication**, **Admin Knowledge Base Management**, **ChromaDB Vector Retrieval**, **HuggingFace Embeddings**, and **Groq Llama 3 LLM Inference**.

---

## 🌟 Features & Highlights

- **User Recognition & Authentication**: JWT-based secure registration and login with role-based access control (`admin` vs `user`).
- **User Conversation Isolation**: Strict per-user database session boundaries (User A cannot view, retrieve, or delete User B's chat history).
- **Admin Knowledge Base Panel**: Admin users can upload document files (**PDF**, **TXT**, **DOCX**), view processing status, and delete files.
- **Dynamic RAG (No LLM Retraining)**: Document chunks and 384-dimensional vector embeddings are stored in a persistent local **ChromaDB** store. Uploading or deleting files dynamically updates chatbot knowledge instantly.
- **Ultra-Fast LLM Inference**: Powered by **Groq Llama 3 API** for sub-second, highly grounded responses with source citations.
- **Strict Answer Grounding & Fallback**: System prompt enforces answer generation solely from Knowledge Base context. If information is not found, a clear fallback message is returned.
- **Modern React SPA UI**: Responsive interface built with React, Vite, Tailwind CSS, React Router, and Axios.

---

## 🏛️ System Architecture

```text
React (Vite + Tailwind SPA)
           │
           ▼
    FastAPI (Python)
    ├── SQLite Database (chatbot.db)
    │   ├── Users & Roles (admin / user)
    │   ├── Conversations & Messages History
    │   └── Knowledge Base Document Metadata
    │
    └── RAG Orchestrator Engine (LangChain)
        ├── Document Loaders (PDF / TXT / DOCX)
        ├── Text Splitter (RecursiveCharacterTextSplitter)
        ├── HuggingFace Embeddings (all-MiniLM-L6-v2)
        ├── ChromaDB (Persistent Vector Store: ./backend/chroma_db)
        └── Groq LLM API (groq/compound-mini / Llama 3)
```

### 🔄 Complete RAG Query Workflow
```text
User Question Input
  ↓
HuggingFace Embedding (all-MiniLM-L6-v2)
  ↓
ChromaDB Vector Similarity Search (top_k=4)
  ↓
Context Extraction & Source Citation Metadata Format
  ↓
System Prompt Engineering + Conversation History Buffer
  ↓
Groq Llama 3 API Inference
  ↓
Answer Generation + Citations JSON Output
  ↓
Save User & Assistant Messages to SQLite
  ↓
Render in React Chat UI
```

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, Vite, Tailwind CSS, React Router v6, Axios, Lucide React |
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy ORM, Pydantic V2, PyJWT, Bcrypt |
| **Database** | SQLite (`chatbot.db`) |
| **Vector Database** | ChromaDB (Local persistent vector store) |
| **RAG & Embeddings** | LangChain, HuggingFace (`all-MiniLM-L6-v2`), `pypdf`, `docx2txt` |
| **LLM Inference** | Groq API (`groq/compound-mini` / Llama 3) |

---

## 📁 Project Structure

```text
chatbot/
├── backend/                        # FastAPI Backend Application
│   ├── app/
│   │   ├── routers/                # API Endpoints (health, auth, admin_kb, chat)
│   │   ├── services/               # Business Logic (vector_service, kb_service, rag_service)
│   │   ├── config.py               # Pydantic Settingsloader
│   │   ├── database.py             # SQLAlchemy Engine & SessionLocal
│   │   ├── deps.py                 # Dependency Injections & RBAC Guards
│   │   ├── main.py                 # FastAPI Entrypoint & CORS Setup
│   │   ├── models.py               # SQLAlchemy ORM Models (User, Conversation, Message, Document)
│   │   ├── schemas.py              # Pydantic DTO Validation Schemas
│   │   ├── security.py             # Password Hashing & JWT Utils
│   │   └── seed_admin.py           # CLI Admin Seeding Script
│   ├── tests/                      # Automated Pytest Suite & Verification Scripts
│   │   ├── test_auth.py
│   │   ├── test_health.py
│   │   ├── test_kb.py
│   │   ├── test_chat.py
│   │   ├── verify_phase2.py
│   │   ├── verify_phase3.py
│   │   └── verify_phase5.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                       # React + Vite Frontend Application
│   ├── src/
│   │   ├── components/             # Navbar, ProtectedRoute
│   │   ├── context/                # AuthContext (JWT & User state)
│   │   ├── pages/                  # LoginPage, RegisterPage, ChatPage, AdminKBPage
│   │   ├── services/               # Axios API Client & Route Services
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css               # Tailwind directives
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example
│
├── .gitignore
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.11+**
- **Node.js v18+** and **npm**
- **Groq API Key** (Get a free key from [Groq Console](https://console.groq.com/))

---

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create local environment configuration
cp .env.example .env
```

Open `.env` in a text editor and set your **GROQ_API_KEY**:
```env
GROQ_API_KEY="gsk_your_actual_groq_api_key"
SECRET_KEY="your_custom_jwt_secret_key"
```

#### Seed Initial Admin User
To safely create the initial Admin user account without hardcoding credentials:
```bash
PYTHONPATH=. ./venv/bin/python -m app.seed_admin --email admin@example.com --password AdminPassword123!
```

#### Start FastAPI Server
```bash
PYTHONPATH=. ./venv/bin/uvicorn app.main:app --reload --port 8000
```
- Interactive API Swagger Documentation: `http://localhost:8000/api/v1/docs`

---

### 2. Frontend Setup

In a new terminal window:

```bash
# Navigate to frontend directory
cd frontend

# Install npm dependencies
npm install

# Create local environment configuration
cp .env.example .env

# Start Vite Development Server
npm run dev
```
- Access the Web Application: `http://localhost:3000` (or `http://localhost:5173`)

---

## 🌐 API Overview

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/v1/health` | Public | System & SQLite connection status |
| `POST` | `/api/v1/auth/register` | Public | Register new user account (`user` role) |
| `POST` | `/api/v1/auth/login` | Public | Authenticate user & return JWT Bearer token |
| `GET` | `/api/v1/auth/me` | Authenticated | Fetch current user profile & role |
| `POST` | `/api/v1/admin/kb/upload` | Admin | Upload PDF/TXT/DOCX file to ChromaDB KB |
| `GET` | `/api/v1/admin/kb/documents` | Admin | List all knowledge base documents |
| `DELETE` | `/api/v1/admin/kb/documents/{id}` | Admin | Delete document file & remove vectors from ChromaDB |
| `GET` | `/api/v1/chat/conversations` | Authenticated | List conversations owned by user |
| `POST` | `/api/v1/chat/conversations` | Authenticated | Create a new conversation session |
| `GET` | `/api/v1/chat/conversations/{id}` | Authenticated | Fetch conversation messages & history |
| `DELETE` | `/api/v1/chat/conversations/{id}` | Authenticated | Delete user conversation session |
| `POST` | `/api/v1/chat/conversations/{id}/message` | Authenticated | Send user prompt, run RAG, return answer + citations |

---

## 🧪 Testing & Verification

### Automated Pytest Suite
Run the backend test suite:
```bash
cd backend
PYTHONPATH=. ./venv/bin/pytest
```
**Test Results**: `18 passed in 2.30s` (Covers Auth, Health, Document Parsing, ChromaDB Vector Cleanup, User Isolation, and RAG QA).

### End-to-End System Validation Script
Run full multi-scenario integration validation:
```bash
cd backend
PYTHONPATH=. ./venv/bin/python tests/verify_phase5.py
```

### Frontend Build Verification
Verify React SPA compilation:
```bash
cd frontend
npm run build
```
**Result**: `✓ built in 3.38s` (0 errors).



<img width="2827" height="1414" alt="image" src="https://github.com/user-attachments/assets/937f9fc7-feff-442d-a2e7-e81ab442cff0" />

<img width="2880" height="1800" alt="image" src="https://github.com/user-attachments/assets/d35b10a5-1031-41d8-8ac4-02814b2177f1" />




<img width="2821" height="1506" alt="image" src="https://github.com/user-attachments/assets/3b9f9268-130f-437a-852d-14d49dec83f5" />


