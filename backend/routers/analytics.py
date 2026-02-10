"""
Analytics Router - HTTP endpoints, dumb on purpose
"""

from fastapi import Depends, APIRouter, Header
from typing import Optional, List, Dict, Any

from services.analytics_service import AnalyticsService
from core.dependencies import get_current_db, verify_authorization

# Explicit import to avoid any circular import issues
from fastapi import Depends as FastAPIDepends


router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/sessions/{session_id}")
async def get_session_analytics(
    session_id: str,
    db=FastAPIDepends(get_current_db),
    user_id: int = Depends(verify_authorization)
) -> Dict[str, Any]:
    """Get analytics for a specific session"""
    # Auth is handled by dependency
    
    analytics = AnalyticsService(db)
    events = analytics.get_session_events(session_id)
    
    return {
        "session_id": session_id,
        "events": events
    }


@router.get("/lessons/{lesson_id}")
async def get_lesson_analytics(
    lesson_id: int,
    db=FastAPIDepends(get_current_db),
    user_id: int = Depends(verify_authorization)
) -> Dict[str, Any]:
    """Get analytics for a specific lesson"""
    # Auth is handled by dependency
    
    analytics = AnalyticsService(db)
    lesson_analytics = analytics.get_lesson_analytics(lesson_id)
    
    return lesson_analytics


@router.get("/users/{user_id}")
async def get_user_analytics(
    user_id: int,
    limit: int = 100,
    db=FastAPIDepends(get_current_db),
    current_user_id: int = Depends(verify_authorization)
) -> Dict[str, Any]:
    """Get analytics for a specific user"""
    # Auth is handled by dependency
    # Verify user ID matches token
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    analytics = AnalyticsService(db)
    events = analytics.get_user_analytics(user_id, limit)
    
    return {
        "user_id": user_id,
        "events": events
    }
