"""
Simple working lessons router
"""

from fastapi import APIRouter, HTTPException, Header
from typing import Optional, List, Dict, Any

from models.lesson import LessonDB
from core.db import get_db_session

router = APIRouter(prefix="/api/lessons", tags=["lessons"])


@router.get("/")
async def get_lessons(authorization: Optional[str] = Header(None)) -> List[Dict[str, Any]]:
    """Get all available lessons"""
    # Simple auth check
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Access token required")
    
    # Get database session
    db = get_db_session()
    
    try:
        lessons = db.query(LessonDB).order_by(LessonDB.created_at.desc()).all()
        return [
            {
                "id": lesson.id,
                "title": lesson.title,
                "schema_version": lesson.schema_version,
                "estimated_duration_minutes": lesson.estimated_duration_minutes,
                "created_at": lesson.created_at.isoformat() if lesson.created_at else None
            }
            for lesson in lessons
        ]
    finally:
        db.close()


@router.get("/{lesson_id}")
async def get_lesson(lesson_id: int, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Get a specific lesson by ID"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Access token required")
    
    db = get_db_session()
    
    try:
        lesson = db.query(LessonDB).filter(LessonDB.id == lesson_id).first()
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        return {
            "id": lesson.id,
            "title": lesson.title,
            "schema_version": lesson.schema_version,
            "estimated_duration_minutes": lesson.estimated_duration_minutes,
            "states": lesson.states  # Raw JSON states
        }
    finally:
        db.close()
