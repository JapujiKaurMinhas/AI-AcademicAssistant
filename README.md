# AI Academic Assistant

A powerful academic assistant built with Python (Backend) and Vanilla JS (Frontend) that uses AI to process PDFs and answer questions.

## Project Structure

The project is organized into two main folders for clarity:

### 📂 [backend/](file:///c:/Users/HP/OneDrive/Desktop/Projects/AI_Academic_Assistant/backend)
- `main.py`: FastAPI server for the AI engine.
- `app.py`: Flask server (alternative).
- `routes/`: API endpoints for QA, Similarity, Voice, etc.
- `services/`: AI logic and PDF processing.
- `models/`: Embeddings and AI models.
- `uploads/`: Directory for uploaded PDF documents.
- `.env`: Environment variables (API keys, etc.).
- `requirements.txt`: Python dependencies.
- `venv/`: Virtual environment.

### 📂 [frontend/](file:///c:/Users/HP/OneDrive/Desktop/Projects/AI_Academic_Assistant/frontend)
- `index.html`: User interface.
- `app.js`: Frontend logic and API integration.
- `style.css`: Modern UI styling.

## How to Run

### Backend
1. Go to the backend folder: `cd backend`
2. Activate venv: `.\venv\Scripts\activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Start the server: `python app.py` (Flask) or `uvicorn main:app --reload` (FastAPI)

### Frontend
- Open `frontend/index.html` in your browser. (Note: You may need a local server or adjust CORS settings in the backend).

## Test the QA Engine
A test script is provided in the backend:
`python backend/test_qa.py`
