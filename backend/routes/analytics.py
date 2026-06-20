from fastapi import APIRouter, Depends
from sqlmodel import Session
from database.db import get_session
from services.analytics_service import get_analytics_report
from models.analytics import AnalyticsStats

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/", response_model=AnalyticsStats)
async def get_stats(session: Session = Depends(get_session)):
    """Retrieves usage statistics and daily activity trends."""
    return get_analytics_report(session)
