# 🎓 AI Academic Assistant

An enterprise-grade, full-stack AI platform designed to transform academic documents (PDFs, research papers, study notes) into interactive learning experiences. Built with **FastAPI**, **React 19**, **Vite**, **Tailwind CSS**, and powered by **Groq Cloud LLMs** (`groq/compound`, `groq/compound-mini`) & **Sentence Transformers**.

---

## 📋 Table of Contents

- [Features](#-features)
- [System Requirements & Prerequisites](#-system-requirements--prerequisites)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Environment Configuration](#-environment-configuration)
- [Quick Start Guide](#-quick-start-guide)
  - [1. Clone Repository](#1-clone-repository)
  - [2. Backend Setup](#2-backend-setup)
  - [3. Frontend Setup](#3-frontend-setup)
- [API Documentation](#-api-documentation)
- [Commit & Push to GitHub](#-commit--push-to-github)
- [License](#-license)

---

## ✨ Features

- 📄 **PDF Processing & Text Extraction**: Upload academic PDFs and extract structural text seamlessly.
- 🧩 **Semantic Text Chunking**: Smart chunking algorithm optimized for context preservation without exceeding token budgets.
- 💬 **RAG Q&A Engine**: Retrieval-Augmented Generation to ask questions directly against uploaded documents.
- ❓ **AI Quiz Generator**: Automatically generate multiple-choice and short-answer quizzes based on document content.
- 🎴 **Interactive Flashcards**: Auto-create study flashcards for quick revision and spaced repetition learning.
- 📈 **Optimization & Benchmark Dashboard**: Real-time tracking of chunking efficiency, token usage, execution latency, and similarity metrics.
- ⚡ **AI Text Modifier**: Summarize, simplify, expand, or retone academic text dynamically.

---

## 💻 System Requirements & Prerequisites

Before running the application, ensure you have the following installed on your system:

| Software | Version Required | Download Link |
| :--- | :--- | :--- |
| **Node.js** | v18.0.0 or higher | [Node.js Official](https://nodejs.org/) |
| **npm** | v9.0.0 or higher | Installed with Node.js |
| **Python** | v3.10, v3.11, or v3.12 | [Python Official](https://www.python.org/) |
| **Git** | Latest | [Git Official](https://git-scm.com/) |

### 🔑 Required API Keys

- **Groq API Key**: Obtain a free/paid API key from [Groq Console](https://console.groq.com/) for fast LLM inference.

---

## 🛠️ Tech Stack

### **Backend**
- **Framework**: FastAPI (Async Python REST API)
- **ASGI Server**: Uvicorn
- **AI & LLM Provider**: Groq API (`groq/compound`, `groq/compound-mini`)
- **Embeddings & Vector Search**: Sentence-Transformers (`all-MiniLM-L6-v2`), PyTorch, Scikit-Learn
- **Database**: SQLite with SQLModel / SQLAlchemy ORM
- **PDF Extraction**: PyPDF2, pdfplumber

### **Frontend**
- **Framework**: React 19 + Vite 8
- **Styling**: Tailwind CSS 4 + Autoprefixer + PostCSS
- **UI & Animations**: Lucide React icons, Framer Motion
- **HTTP Client**: Axios
- **Routing**: React Router DOM v7

---

## 📂 Project Structure

```
AI_Academic_Assistant/
├── backend/                  # FastAPI Application
│   ├── database/             # SQLite DB models & connection
│   ├── models/               # Pydantic & SQLModel schemas
│   ├── routes/               # API route handlers (qa, document, quiz, flashcard, benchmark, etc.)
│   ├── services/             # Core business & AI logic
│   ├── uploads/              # Uploaded PDF storage directory
│   ├── utils/                # Text chunker, QA engine, AI modifiers, PDF extractors
│   ├── .env.example          # Environment variable template
│   ├── config.py             # Centralized token budgets & model parameters
│   ├── main.py               # FastAPI application entry point
│   └── requirements.txt      # Python dependencies
│
├── frontend/                 # React + Vite Application
│   ├── public/               # Static assets
│   ├── src/
│   │   ├── components/       # UI Components (Navbar, Cards, Uploaders, Modals)
│   │   ├── pages/            # View pages (Home, Upload, Q&A, Quiz, Analytics, Benchmark)
│   │   ├── services/         # Axios API clients
│   │   ├── App.jsx           # Application routing & layout
│   │   └── main.jsx          # React app entry point
│   ├── package.json          # Node.js dependencies & scripts
│   ├── vite.config.js        # Vite bundler configuration
│   └── tailwind.config.js    # Tailwind CSS configuration
│
├── .gitignore                # Git ignore patterns
└── README.md                 # Project documentation
```

---

## ⚙️ Environment Configuration

1. Navigate to the `backend/` directory.
2. Create a `.env` file from `.env.example`:

```bash
cd backend
cp .env.example .env
```

3. Update `.env` with your credentials:

```env
GROQ_API_KEY=your_actual_groq_api_key_here
DATABASE_URL=sqlite:///./academic_assistant.db
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
PORT=8000
```

---

## 🚀 Quick Start Guide

### 1. Clone Repository

```bash
git clone https://github.com/JapujiKaurMinhas/AI-AcademicAssistant.git
cd AI-AcademicAssistant
```

### 2. Backend Setup

Open a terminal in the root directory:

```bash
# Navigate to backend directory
cd backend

# Create Python virtual environment
python -m venv venv

# Activate Virtual Environment
# Windows PowerShell:
.\venv\Scripts\activate
# macOS / Linux:
# source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Start FastAPI server
python main.py
# Or using uvicorn directly:
# uvicorn main:app --reload --port 8000
```

> 🌐 Backend API will be live at: **`http://127.0.0.1:8000`**  
> 📖 Interactive Swagger API Docs: **`http://127.0.0.1:8000/docs`**

---

### 3. Frontend Setup

Open a new terminal window in the root directory:

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```

> 🖥️ Web App will be running at: **`http://localhost:5173`** (or `http://localhost:5174`)

---

## 🔌 API Documentation

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `GET /` | `GET` | Health check & API version status |
| `POST /upload/` | `POST` | Upload PDF file & trigger automatic text extraction |
| `POST /qa/ask` | `POST` | Ask questions against uploaded document context (RAG) |
| `POST /quiz/generate` | `POST` | Generate interactive quiz questions from document text |
| `POST /flashcard/generate` | `POST` | Auto-generate flashcards for study revision |
| `GET /analysis/` | `GET` | Retrieve semantic document analysis & key takeaways |
| `GET /benchmark/` | `GET` | Retrieve system benchmark & performance comparison |

---

## 📤 Commit & Push to GitHub

To commit your latest changes and upload them to GitHub:

```bash
# Check status of modified files
git status

# Stage all updated files
git add .

# Commit changes with a message
git commit -m "docs: add comprehensive README with requirements and setup guide"

# Push changes to GitHub
git push origin main
```

---

## 📄 License

Distributed under the **MIT License**. See `backend/LICENSE` for details.
