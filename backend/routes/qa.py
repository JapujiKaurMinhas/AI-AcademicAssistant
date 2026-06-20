from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from database.db import get_session
from services.ai_service import generate_explanation, extract_topics
from services.analytics_service import log_event
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/qa", tags=["QA"])

class QuestionRequest(BaseModel):
    question: str
    context: Optional[str] = ""

class QuestionResponse(BaseModel):
    answer: str
    topic: str
    status: str = "success"

@router.post("/ask", response_model=QuestionResponse)
async def ask_question(req: QuestionRequest, session: Session = Depends(get_session)):
    """Handles text-based and voice-derived AI questions."""
    if not req.question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # Generate explanation from Groq
    answer = generate_explanation(req.question, req.context)
    
    # Extract topics for analytics
    topic_str = extract_topics(req.question)
    
    # Log usage event
    log_event(session, "question", topic=topic_str)
    
    return QuestionResponse(answer=answer, topic=topic_str)