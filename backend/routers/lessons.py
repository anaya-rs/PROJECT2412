"""
Lessons Router - HTTP endpoints, dumb on purpose
"""

from fastapi import Depends, APIRouter, HTTPException
from typing import Optional, List, Dict, Any
import json

from core.dependencies import get_current_db, verify_authorization, get_db_session
from services.lesson_generation import LessonGenerator, LessonGenerationError
from models.lesson import LessonDB
from core.config import get_settings

# Explicit import to avoid any circular import issues
from fastapi import Depends as FastAPIDepends


router = APIRouter(prefix="/api/lessons", tags=["lessons"])


@router.get("/")
async def get_lessons(
    db=FastAPIDepends(get_current_db),
    user_id: int = Depends(verify_authorization)
) -> List[Dict[str, Any]]:
    """Get all available lessons"""
    # Auth is handled by dependency
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
async def get_lesson(
    lesson_id: int, 
    db=FastAPIDepends(get_current_db),
    user_id: int = Depends(verify_authorization)
) -> Dict[str, Any]:
    """Get a specific lesson by ID"""
    # Auth is handled by dependency
    try:
        lesson = db.query(LessonDB).filter(LessonDB.id == lesson_id).first()
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        return {
            "id": lesson.id,
            "title": lesson.title,
            "schema_version": lesson.schema_version,
            "estimated_duration_minutes": lesson.estimated_duration_minutes,
            "states": json.loads(lesson.states)  # Parse JSON states
        }
    finally:
        db.close()


@router.delete("/{lesson_id}")
async def delete_lesson(
    lesson_id: int, 
    db=FastAPIDepends(get_current_db),
    user_id: int = Depends(verify_authorization)
) -> Dict[str, Any]:
    """Delete a lesson by ID"""
    # Auth is handled by dependency
    try:
        lesson = db.query(LessonDB).filter(LessonDB.id == lesson_id).first()
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        db.delete(lesson)
        db.commit()
        
        return {"message": "Lesson deleted successfully"}
    finally:
        db.close()


@router.post("/generate")
async def generate_lesson(
    request: Dict[str, Any],
    db=FastAPIDepends(get_current_db),
    user_id: int = Depends(verify_authorization)
) -> Dict[str, Any]:
    """Generate a new lesson using LLM"""
    # Auth is handled by dependency
    
    # Validate input
    if "text" not in request or len(request["text"]) < 100:
        raise HTTPException(status_code=400, detail="Text content is too short (minimum 100 characters)")
    
    duration = request.get("duration", 30)
    if duration not in [5, 30, 60]:
        raise HTTPException(status_code=400, detail="Duration must be 5, 30, or 60 minutes")
    
    try:
        settings = get_settings()
        generator = LessonGenerator(
            ollama_url=settings.OLLAMA_URL,
            model=settings.OLLAMA_MODEL,
            db_session=db
        )
        
        lesson_id = generator.generate_lesson(
            content=request["text"],
            title=request.get("title", ""),
            description=request.get("description", ""),
            duration_minutes=duration,
            difficulty=request.get("difficulty", "beginner")
        )
        
        return {
            "lesson_id": lesson_id,
            "message": "Lesson generated successfully"
        }
        
    except LessonGenerationError as e:
        raise HTTPException(status_code=500, detail=str(e))
