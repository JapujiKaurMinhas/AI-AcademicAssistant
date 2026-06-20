from sqlmodel import Session, select, func
from datetime import datetime, timedelta
from typing import List, Dict
from models.analytics import UsageEvent, AnalyticsStats
from database.db import engine

def log_event(session: Session, event_type: str, topic: str = None, details: str = None):
    """Log a usage event to the database for analytics."""
    event = UsageEvent(event_type=event_type, topic=topic, details=details)
    session.add(event)
    session.commit()
    session.refresh(event)
    return event

def get_analytics_report(session: Session) -> AnalyticsStats:
    """Aggregates data to generate a full analytics report."""
    
    # Total counts
    total_q = session.exec(select(func.count(UsageEvent.id)).where(UsageEvent.event_type == 'question')).one()
    total_u = session.exec(select(func.count(UsageEvent.id)).where(UsageEvent.event_type == 'upload')).one()
    total_s = session.exec(select(func.count(UsageEvent.id)).where(UsageEvent.event_type == 'similarity')).one()
    
    # Topic distribution (top 10)
    topic_query = session.exec(select(UsageEvent.topic)).all()
    topic_counts = {}
    for t in topic_query:
        if not t: continue
        # Handle comma-separated keywords if LLM returns multiple
        keywords = [kw.strip() for kw in str(t).split(",")]
        for kw in keywords[:2]: # only take top 2 to keep charts clean
            topic_counts[kw] = topic_counts.get(kw, 0) + 1
            
    sorted_topics = dict(sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10])

    # Simple activity timeline (last 7 days)
    last_week = datetime.utcnow() - timedelta(days=7)
    activity_query = session.exec(select(UsageEvent.timestamp, UsageEvent.event_type).where(UsageEvent.timestamp >= last_week)).all()
    
    # Format timeline (Daily frequency)
    timeline_data = {}
    for ts, etype in activity_query:
        day = ts.strftime("%Y-%m-%d")
        if day not in timeline_data:
            timeline_data[day] = 0
        timeline_data[day] += 1
    
    formatted_timeline = [{"day": k, "count": v} for k, v in sorted(timeline_data.items())]

    return AnalyticsStats(
        total_questions=total_q,
        total_uploads=total_u,
        total_similarity_checks=total_s,
        topic_distribution=sorted_topics,
        activity_timeline=formatted_timeline
    )
