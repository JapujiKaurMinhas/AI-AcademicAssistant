from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import Optional
from pydantic import BaseModel
from database.db import get_session
from models.quiz import QuizAttempt
from models.processed_document import ProcessedDocument
from services.ai_service import generate_document_intel
from utils.quiz_generator import generate_quiz_from_context
from services.document_service import extract_text_from_pdf
from sqlmodel import select
import os

router = APIRouter(prefix="/api/quiz", tags=["Quiz"])

class QuizSubmission(BaseModel):
    score: int
    total_questions: int

@router.get("/generate")
async def generate_quiz(filename: Optional[str] = Query(None), session: Session = Depends(get_session)):
    """Generates a quiz based on the currently uploaded document."""
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
    if not os.path.exists(upload_dir) or not os.listdir(upload_dir):
        raise HTTPException(status_code=400, detail="No document uploaded. Please upload a PDF first.")
    
    # Get specific pdf or latest pdf
    if filename:
        target_filename = filename
        latest_file = os.path.join(upload_dir, filename)
        if not os.path.exists(latest_file):
            raise HTTPException(status_code=404, detail="Specified PDF not found.")
    else:
        pdfs = [os.path.join(upload_dir, f) for f in os.listdir(upload_dir) if f.endswith('.pdf')]
        if not pdfs:
            raise HTTPException(status_code=400, detail="No PDF found. Please upload a PDF first.")
        latest_file = max(pdfs, key=os.path.getmtime)
        target_filename = os.path.basename(latest_file)
    
    # Look up in ProcessedDocument table
    try:
        statement = select(ProcessedDocument).where(ProcessedDocument.filename == target_filename)
        processed_doc = session.exec(statement).first()
    except Exception as db_err:
        print(f"!!! DB error in quiz route: {db_err}")
        processed_doc = None

    if processed_doc:
        # Check size: if small, use raw text. If large, use summary + key concepts context
        if len(processed_doc.extracted_text) < 12000:
            context = processed_doc.extracted_text
        else:
            context = f"EXECUTIVE SUMMARY:\n{processed_doc.summary}\n\nCORE CONCEPT NOTES:\n{processed_doc.key_points}"
    else:
        # Fallback: process document now and save to DB
        with open(latest_file, "rb") as f:
            file_content = f.read()
            
        extracted_text = extract_text_from_pdf(file_content)
        if not extracted_text or "Error reading" in extracted_text:
            raise HTTPException(status_code=500, detail="Failed to extract text from the PDF.")
        
        try:
            summary, key_points = generate_document_intel(extracted_text, filename=target_filename, session=session)
            if len(extracted_text) < 12000:
                context = extracted_text
            else:
                context = f"EXECUTIVE SUMMARY:\n{summary}\n\nCORE CONCEPT NOTES:\n{key_points}"
        except Exception as e:
            # Fallback to truncated raw text if intel generation fails
            context = extracted_text[:10000]
    
    questions = generate_quiz_from_context(context, num_questions=5)
    if not questions:
        raise HTTPException(status_code=500, detail="Failed to generate quiz. Please try again.")
        
    return {"questions": questions}

@router.post("/submit")
async def submit_quiz(submission: QuizSubmission, session: Session = Depends(get_session)):
    """Saves the quiz score to the database."""
    attempt = QuizAttempt(score=submission.score, total_questions=submission.total_questions)
    session.add(attempt)
    session.commit()
    session.refresh(attempt)
    return {"message": "Score saved successfully", "attempt_id": attempt.id}

@router.get("/history")
async def get_quiz_history(session: Session = Depends(get_session)):
    """Retrieves all past quiz attempts."""
    from sqlmodel import select
    attempts = session.exec(select(QuizAttempt).order_by(QuizAttempt.created_at.desc())).all()
    return {"history": attempts}
