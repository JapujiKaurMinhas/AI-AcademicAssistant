import os
import uuid
import asyncio
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlmodel import Session
from database.db import get_session
from pydantic import BaseModel
from services.document_service import extract_text_from_pdf
from services.ai_service import generate_document_intel, async_generate_document_intel
from services.analytics_service import log_event
from utils.youtube_helper import extract_transcript
from typing import Optional, List

router = APIRouter(prefix="/api/document", tags=["Document"])

# Global in-memory progress store for background synthesis tasks
tasks_progress = {}

class UploadResponse(BaseModel):
    filename: str
    text: str
    summary: Optional[str] = None
    key_points: Optional[str] = None
    status: str = "success"

class AsyncTaskResponse(BaseModel):
    task_id: str
    filename: str
    status: str = "processing"

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str          # "processing", "completed", "failed"
    progress: int        # 0 to 100
    phase: str          # Descriptive stage message
    filename: str
    result: Optional[UploadResponse] = None
    error: Optional[str] = None

class DocumentInfo(BaseModel):
    filename: str
    upload_date: str
    size: str

class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]

async def process_document_task(task_id: str, text: str, filename: str, session: Session):
    """Background task worker that calls the optimized async synthesis engine and reports progress."""
    tasks_progress[task_id] = {
        "status": "processing",
        "progress": 5,
        "phase": "Starting document analysis...",
        "filename": filename,
        "result": None,
        "error": None
    }
    
    async def progress_callback(percent: int, phase: str):
        if task_id in tasks_progress:
            tasks_progress[task_id]["progress"] = percent
            tasks_progress[task_id]["phase"] = phase

    try:
        # Call the optimized async core synthesis engine
        summary, key_points = await async_generate_document_intel(
            text=text, 
            filename=filename, 
            session=session, 
            progress_callback=progress_callback
        )
        
        # Store final completion result
        tasks_progress[task_id] = {
            "status": "completed",
            "progress": 100,
            "phase": "Completed",
            "filename": filename,
            "result": {
                "filename": filename,
                "text": text,
                "summary": summary,
                "key_points": key_points
            },
            "error": None
        }
    except Exception as e:
        print(f"!!! Error in process_document_task for {filename}: {str(e)}")
        tasks_progress[task_id] = {
            "status": "failed",
            "progress": 100,
            "phase": "Error",
            "filename": filename,
            "result": None,
            "error": f"AI processing failed: {str(e)}"
        }

@router.post("/upload", response_model=AsyncTaskResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    """Uploads a PDF, extracts text, and triggers AI insights generation in the background."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    print(f"--- Initiating Async Upload: {file.filename} ---")
    content = await file.read()
    
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    
    # Save file to uploads folder for listing in dashboard
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(content)
        
    # Extract text (run in thread pool to prevent blocking the FastAPI async event loop)
    extracted_text = await asyncio.to_thread(extract_text_from_pdf, content)
    
    if not extracted_text or len(extracted_text) < 10:
        extracted_text = f"Warning: The document '{file.filename}' appears to be empty or contains only images."
        
    if "Error" in extracted_text:
        raise HTTPException(status_code=500, detail=extracted_text)
        
    # Generate task ID and launch background worker
    task_id = str(uuid.uuid4())
    background_tasks.add_task(process_document_task, task_id, extracted_text, file.filename, session)
    
    # Log usage event
    log_event(session, "upload")
    print(f"--- Async Job Enqueued for {file.filename} with task_id: {task_id} ---")
    
    return AsyncTaskResponse(task_id=task_id, filename=file.filename)

@router.get("/intel", response_model=AsyncTaskResponse)
async def get_existing_document_intel(
    background_tasks: BackgroundTasks,
    filename: str,
    session: Session = Depends(get_session)
):
    """Triggers AI insights generation in the background for a previously uploaded PDF."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    upload_dir = os.path.join(os.path.dirname(current_dir), "uploads")
    file_path = os.path.join(upload_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found.")
        
    def read_file():
        with open(file_path, "rb") as f:
            return f.read()
            
    content = await asyncio.to_thread(read_file)
    extracted_text = await asyncio.to_thread(extract_text_from_pdf, content)
    
    if not extracted_text or "Error" in extracted_text:
        raise HTTPException(status_code=500, detail="Failed to extract text from PDF.")
        
    task_id = str(uuid.uuid4())
    background_tasks.add_task(process_document_task, task_id, extracted_text, filename, session)
    
    log_event(session, "generate_notes")
    
    return AsyncTaskResponse(task_id=task_id, filename=filename)

class YoutubeRequest(BaseModel):
    url: str

@router.post("/youtube", response_model=AsyncTaskResponse)
async def generate_youtube_intel(
    req: YoutubeRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    """Triggers AI insights generation in the background from a YouTube video transcript."""
    extracted_text = await asyncio.to_thread(extract_transcript, req.url)
    if not extracted_text:
        raise HTTPException(status_code=400, detail="Failed to extract transcript. Make sure the video has closed captions/subtitles enabled.")
        
    task_id = str(uuid.uuid4())
    background_tasks.add_task(process_document_task, task_id, extracted_text, req.url, session)
    
    log_event(session, "generate_notes")
    
    return AsyncTaskResponse(task_id=task_id, filename=req.url)

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Retrieves progress and execution state for a given background synthesis task."""
    if task_id not in tasks_progress:
        raise HTTPException(status_code=404, detail="Task not found.")
        
    task = tasks_progress[task_id]
    
    result_data = None
    if task["status"] == "completed" and task["result"]:
        result_data = UploadResponse(**task["result"])
        
    return TaskStatusResponse(
        task_id=task_id,
        status=task["status"],
        progress=task["progress"],
        phase=task["phase"],
        filename=task["filename"],
        result=result_data,
        error=task["error"]
    )

@router.get("/list", response_model=DocumentListResponse)
def list_documents():
    """Returns a list of all uploaded PDF documents from the uploads directory."""
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
    docs.sort(key=lambda x: x.upload_date, reverse=True)
    return DocumentListResponse(documents=docs)

@router.delete("/delete")
def delete_document(filename: str):
    """Deletes a previously uploaded PDF document from the uploads directory."""
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
