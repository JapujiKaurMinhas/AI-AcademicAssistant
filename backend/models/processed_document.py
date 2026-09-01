from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class ProcessedDocument(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(unique=True, index=True)  # File name or identifier (e.g. YouTube URL)
    extracted_text: str
    chunks_json: str  # JSON list of chunk-level summaries and notes
    summary: str      # Final Executive Summary
    key_points: str   # Final Core Concept Notes
    created_at: datetime = Field(default_factory=datetime.utcnow)
