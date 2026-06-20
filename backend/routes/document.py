import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlmodel import Session
from database.db import get_session
from pydantic import BaseModel
from services.document_service import extract_text_from_pdf
from services.ai_service import generate_document_intel
from services.analytics_service import log_event
from utils.youtube_helper import extract_transcript
from typing import Optional, List

router = APIRouter(prefix="/api/document", tags=["Document"])

class UploadResponse(BaseModel):
    filename: str
    text: str
    summary: Optional[str] = None
    key_points: Optional[str] = None
    status: str = "success"

@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...), session: Session = Depends(get_session)):
    """Uploads a PDF, extracts text, and generates AI insights (Summary & Key Points)."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    print(f"--- Processing Upload: {file.filename} ---")
    content = await file.read()
    
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    # Save to disk for persistence and dashboard listing
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(content)

    extracted_text = extract_text_from_pdf(content)
    
    if not extracted_text or len(extracted_text) < 10:
        extracted_text = f"Warning: The document '{file.filename}' appears to be empty or contains only images. Semantic analysis might be limited."
        print(f"!!! PDF Extraction Warning: {extracted_text}")
    
    if "Error" in extracted_text:
        print(f"!!! PDF Extraction Error: {extracted_text}")
        raise HTTPException(status_code=500, detail=extracted_text)
    
    # Generate Insights in a single optimized call
    print(f"--- Generating AI Intel for {len(extracted_text)} chars ---")
    ai_summary, ai_key_points = generate_document_intel(extracted_text)
    
    # Log usage event
    log_event(session, "upload")
    print(f"--- Upload Complete for {file.filename} ---")
    
    return UploadResponse(
        filename=file.filename,
        text=extracted_text,
        summary=ai_summary,
        key_points=ai_key_points
    )

@router.get("/intel", response_model=UploadResponse)
def get_existing_document_intel(filename: str, session: Session = Depends(get_session)):
    """Generates AI insights (Summary & Key Points) for a previously uploaded PDF."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    upload_dir = os.path.join(os.path.dirname(current_dir), "uploads")
    file_path = os.path.join(upload_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found.")
        
    with open(file_path, "rb") as f:
        content = f.read()
        
    extracted_text = extract_text_from_pdf(content)
    if not extracted_text or "Error" in extracted_text:
        raise HTTPException(status_code=500, detail="Failed to extract text from PDF.")
        
    ai_summary, ai_key_points = generate_document_intel(extracted_text)
    
    log_event(session, "generate_notes")
    
    return UploadResponse(
        filename=filename,
        text=extracted_text,
        summary=ai_summary,
        key_points=ai_key_points
    )

class YoutubeRequest(BaseModel):
    url: str

@router.post("/youtube", response_model=UploadResponse)
def generate_youtube_intel(req: YoutubeRequest, session: Session = Depends(get_session)):
    """Generates AI insights from a YouTube video transcript."""
    extracted_text = extract_transcript(req.url)
    if not extracted_text:
        raise HTTPException(status_code=400, detail="Failed to extract transcript. Make sure the video has closed captions/subtitles enabled.")
    
    print(f"--- Generating AI Intel for YouTube video ({len(extracted_text)} chars) ---")
    ai_summary, ai_key_points = generate_document_intel(extracted_text)
    
    log_event(session, "generate_notes")
    
    return UploadResponse(
        filename="YouTube Video Notes",
        text=extracted_text,
        summary=ai_summary,
        key_points=ai_key_points
    )


class DocumentInfo(BaseModel):
    filename: str
    upload_date: str
    size: str

class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]

@router.get("/list", response_model=DocumentListResponse)
def list_documents():
    """Returns a list of all uploaded PDF documents from the uploads directory."""
    # The uploads directory is at project root (AI_Academic_Assistant/backend/uploads)
    # This route assumes we are in AI_Academic_Assistant/backend/routes/document.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    upload_dir = os.path.join(os.path.dirname(current_dir), "uploads")
    
    if not os.path.exists(upload_dir):
        return DocumentListResponse(documents=[])
    
    import datetime
    docs = []
    for f in os.listdir(upload_dir):
        if f.endswith(".pdf"):
            path = os.path.join(upload_dir, f)
            stats = os.stat(path)
            docs.append(DocumentInfo(
                filename=f,
                upload_date=datetime.datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M"),
                size=f"{stats.st_size / 1024 / 1024:.2f} MB"
            ))
    # Sort by upload date (newest first)
    docs.sort(key=lambda x: x.upload_date, reverse=True)
    return DocumentListResponse(documents=docs)

@router.delete("/delete")
def delete_document(filename: str):
    """Deletes a previously uploaded PDF document from the uploads directory."""
    # Prevent path traversal attacks
    safe_filename = os.path.basename(filename)
    if not safe_filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files can be deleted.")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    upload_dir = os.path.join(os.path.dirname(current_dir), "uploads")
    file_path = os.path.join(upload_dir, safe_filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found.")
    
    try:
        os.remove(file_path)
        return {"message": f"'{safe_filename}' has been deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
