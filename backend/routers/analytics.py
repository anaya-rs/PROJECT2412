"""
analytics router
"""

from fastapi import Depends, APIRouter, Header
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from services.analytics_service import AnalyticsService
from core.dependencies import get_db, verify_authorization


router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/sessions/{session_id}")
async def get_session_analytics(
    session_id: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(verify_authorization)
) -> Dict[str, Any]:
    """get analytics for a specific session"""
    
    analytics = AnalyticsService(db)
    events = analytics.get_session_events(session_id)
    
    # verify user owns this session
    if events and events.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "session_id": session_id,
        "events": events
    }


@router.get("/lessons/{lesson_id}")
async def get_lesson_analytics(
    lesson_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(verify_authorization)
) -> Dict[str, Any]:
    """get analytics for a specific lesson"""
    
    analytics = AnalyticsService(db)
    lesson_analytics = analytics.get_lesson_analytics(lesson_id)
    
    # verify user has access to this lesson (simplified - could be enhanced)
    if lesson_analytics and lesson_analytics.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return lesson_analytics


@router.get("/users/{user_id}")
async def get_user_analytics(
    user_id: int,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_authorization)
) -> Dict[str, Any]:
    """get analytics for a specific user"""

    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    analytics = AnalyticsService(db)
    events = analytics.get_user_analytics(user_id, limit)
    
    return {
        "user_id": user_id,
        "events": events
    }
