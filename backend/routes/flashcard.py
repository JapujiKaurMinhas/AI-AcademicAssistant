from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from utils.flashcard_generator import generate_flashcards_from_context
from services.document_service import extract_text_from_pdf
import os

router = APIRouter(prefix="/api/flashcards", tags=["Flashcards"])

@router.get("/generate")
async def generate_flashcards(filename: Optional[str] = Query(None), count: int = Query(10, ge=5, le=20)):
    """Generates flashcards based on an uploaded PDF document."""
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
    if not os.path.exists(upload_dir) or not os.listdir(upload_dir):
        raise HTTPException(status_code=400, detail="No document uploaded. Please upload a PDF first.")
    
    # Get specific pdf or latest pdf
    if filename:
        target_file = os.path.join(upload_dir, filename)
        if not os.path.exists(target_file):
            raise HTTPException(status_code=404, detail="Specified PDF not found.")
    else:
        pdfs = [os.path.join(upload_dir, f) for f in os.listdir(upload_dir) if f.endswith('.pdf')]
        if not pdfs:
            raise HTTPException(status_code=400, detail="No PDF found. Please upload a PDF first.")
        target_file = max(pdfs, key=os.path.getmtime)
    
    with open(target_file, "rb") as f:
        file_content = f.read()
        
    context = extract_text_from_pdf(file_content)
    if not context or "Error reading" in context:
        raise HTTPException(status_code=500, detail="Failed to extract text from the PDF.")
    
    flashcards = generate_flashcards_from_context(context, num_cards=count)
    if not flashcards:
        raise HTTPException(status_code=500, detail="Failed to generate flashcards. Please try again.")
        
    return {"flashcards": flashcards, "source": os.path.basename(target_file), "total": len(flashcards)}
