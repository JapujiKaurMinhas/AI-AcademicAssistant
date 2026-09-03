import os
import sys
from dotenv import load_dotenv

# Add the current directory (backend) to sys.path so we can import from database/routes/etc.
# This fixes the "Attempted relative import" error for any direct execution.
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

# Load .env first before ANY other imports
load_dotenv(os.path.join(CURRENT_DIR, ".env"))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# USE ABSOLUTE IMPORTS (Relative imports fail if run directly)
from database.db import create_db_and_tables
from routes import qa, document, analysis, analytics, quiz, flashcard, benchmark, optimization

# Initialize Database on Startup
create_db_and_tables()

app = FastAPI(
    title="Intelligent AI Academic Assistant",
    description="A production-ready Enterprise AI backend with Voice & Semantic Analysis.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(qa.router)
app.include_router(document.router)
app.include_router(analysis.router)
app.include_router(analytics.router)
app.include_router(quiz.router)
app.include_router(flashcard.router)
app.include_router(benchmark.router)
app.include_router(optimization.router)

@app.get("/")
def root():
    return {
        "message": "AI Academic Assistant API is Live!",
        "docs_url": "/docs",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    # Disable reload for maximum stability during production-like testing
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)