import os
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database.db import get_session
from services.ai_service import generate_explanation, extract_topics
from services.analytics_service import log_event
from services.document_service import extract_text_from_pdf
from models.processed_document import ProcessedDocument
from utils.text_chunker import split_text_into_chunks, get_embedding_model
from optimization.active_config import get_active_config, RetrievalConfig
from optimization.evaluation import cosine_similarity, estimate_tokens
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

router = APIRouter(prefix="/api/qa", tags=["QA"])

class QuestionRequest(BaseModel):
    question: str
    context: Optional[str] = ""
    retrieval_mode: Optional[str] = None       # "default" or "optimized"
    document_filename: Optional[str] = None

class QuestionResponse(BaseModel):
    answer: str
    topic: str
    status: str = "success"
    sources: Optional[List[str]] = []
    retrieval_mode: Optional[str] = "default"
    retrieval_config: Optional[Dict[str, Any]] = None

def retrieve_document_context(
    query: str,
    doc_text: str,
    chunk_size: int,
    chunk_overlap: int,
    top_k: int,
    threshold: float,
    budget: int
) -> tuple[str, List[str]]:
    """Performs real vector retrieval over document text using specified parameters."""
    chunks = split_text_into_chunks(doc_text, chunk_size=chunk_size, overlap=chunk_overlap)
    if not chunks:
        return "", []

    model = get_embedding_model()
    q_emb = model.encode(query, show_progress_bar=False)
    c_embs = model.encode(chunks, show_progress_bar=False)

    sims = [cosine_similarity(q_emb, ce) for ce in c_embs]
    ranked_indices = np.argsort(sims)[::-1]

    selected_chunks = []
    source_snippets = []
    accumulated_tokens = 0

    for idx in ranked_indices:
        if len(selected_chunks) >= top_k:
            break
        sim = sims[idx]
        if sim < threshold:
            continue
        
        chunk = chunks[idx]
        tokens = estimate_tokens(chunk)
        if accumulated_tokens + tokens > budget:
            if not selected_chunks:
                selected_chunks.append(chunk)
                source_snippets.append(f"Chunk #{idx+1} (sim: {sim:.2f})")
            break

        selected_chunks.append(chunk)
        accumulated_tokens += tokens
        snippet = f"Chunk #{idx+1} (sim: {sim:.2f}): {chunk[:100]}..."
        source_snippets.append(snippet)

    assembled_context = "\n\n---\n\n".join(selected_chunks)
    return assembled_context, source_snippets

@router.post("/ask", response_model=QuestionResponse)
async def ask_question(req: QuestionRequest, session: Session = Depends(get_session)):
    """Handles text-based and voice-derived AI questions with optimization-driven retrieval."""
    if not req.question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # 1. Determine Retrieval Configuration
    active_cfg = get_active_config()
    mode = req.retrieval_mode or active_cfg.mode

    if mode == "optimized":
        cfg = active_cfg
    else:
        # Default baseline configuration
        cfg = RetrievalConfig(
            chunk_size=800,
            chunk_overlap=100,
            top_k=3,
            similarity_threshold=0.20,
            context_token_budget=3000,
            mode="default",
            algorithm_source="Manual Default"
        )

    context = req.context or ""
    sources = []

    # 2. If no context was provided directly, retrieve dynamically from document
    if not context.strip():
        doc_text = ""
        # Look for target document or latest uploaded PDF
        if req.document_filename:
            p_doc = session.exec(select(ProcessedDocument).where(ProcessedDocument.filename == req.document_filename)).first()
            if p_doc and p_doc.extracted_text:
                doc_text = p_doc.extracted_text
            else:
                upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
                fpath = os.path.join(upload_dir, req.document_filename)
                if os.path.exists(fpath):
                    with open(fpath, "rb") as f:
                        doc_text = extract_text_from_pdf(f.read())
        else:
            # Check latest ProcessedDocument in database
            latest_doc = session.exec(select(ProcessedDocument).order_by(ProcessedDocument.created_at.desc())).first()
            if latest_doc and latest_doc.extracted_text:
                doc_text = latest_doc.extracted_text
            else:
                # Check uploads folder for any pdf
                upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
                if os.path.exists(upload_dir):
                    pdfs = [os.path.join(upload_dir, f) for f in os.listdir(upload_dir) if f.endswith(".pdf")]
                    if pdfs:
                        latest_pdf = max(pdfs, key=os.path.getmtime)
                        with open(latest_pdf, "rb") as f:
                            doc_text = extract_text_from_pdf(f.read())

        if doc_text and not doc_text.startswith("Error"):
            context, sources = retrieve_document_context(
                query=req.question,
                doc_text=doc_text,
                chunk_size=cfg.chunk_size,
                chunk_overlap=cfg.chunk_overlap,
                top_k=cfg.top_k,
                threshold=cfg.similarity_threshold,
                budget=cfg.context_token_budget
            )

    # 3. Generate explanation from LLM using retrieved context
    answer = generate_explanation(req.question, context)
    
    # 4. Extract topics for analytics
    topic_str = extract_topics(req.question)
    
    # Log usage event
    log_event(session, "question", topic=topic_str)
    
    return QuestionResponse(
        answer=answer,
        topic=topic_str,
        sources=sources,
        retrieval_mode=mode,
        retrieval_config=cfg.to_dict()
    )