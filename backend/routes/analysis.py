from fastapi import APIRouter, Depends
from sqlmodel import Session
from database.db import get_session
from services.semantic_service import analyze_semantic_meaning, get_similarity_score
from services.analytics_service import log_event
from utils.ai_modifier import detect_plagiarism, humanize_text
from pydantic import BaseModel

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])

class ComparisonRequest(BaseModel):
    paragraph1: str
    paragraph2: str

class SemanticResponse(BaseModel):
    score: float
    percentage: float
    match_level: str

@router.post("/similarity", response_model=float)
async def check_similarity(req: ComparisonRequest, session: Session = Depends(get_session)):
    """Computes basic cosine similarity score between two paragraphs."""
    log_event(session, "similarity")
    return get_similarity_score(req.paragraph1, req.paragraph2)

@router.post("/semantic-analysis", response_model=SemanticResponse)
async def semantic_analysis(req: ComparisonRequest, session: Session = Depends(get_session)):
    """Determines semantic meaning matching level between two sentences/paragraphs."""
    log_event(session, "semantic")
    result = analyze_semantic_meaning(req.paragraph1, req.paragraph2)
    return SemanticResponse(**result)

class TextRequest(BaseModel):
    text: str

@router.post("/detect-plagiarism")
async def check_plagiarism(req: TextRequest, session: Session = Depends(get_session)):
    """Checks for AI generation / Plagiarism in text."""
    log_event(session, "plagiarism_check")
    result = detect_plagiarism(req.text)
    return result

@router.post("/humanize")
async def humanize(req: TextRequest, session: Session = Depends(get_session)):
    """Rewrites text to sound more human."""
    log_event(session, "humanize_text")
    result = humanize_text(req.text)
    return {"humanized_text": result}

