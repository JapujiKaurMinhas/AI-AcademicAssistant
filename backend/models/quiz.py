from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class QuizAttempt(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    score: int
    total_questions: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
