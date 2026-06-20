from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class UsageEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_type: str  # 'question', 'upload', 'similarity', 'semantic'
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    topic: Optional[str] = None  # Key topic extracted from the question
    details: Optional[str] = None  # Extra info if needed

class AnalyticsStats(SQLModel):
    total_questions: int
    total_uploads: int
    total_similarity_checks: int
    topic_distribution: dict
    activity_timeline: list
