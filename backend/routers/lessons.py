"""
lessons router
"""

from fastapi import Depends, APIRouter, HTTPException
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import json

from core.dependencies import get_db, verify_authorization
from services.openai_lesson_generator import OpenAILessonGenerator, StatewiseGenerationError
from models.lesson import LessonDB
from core.config import settings


router = APIRouter(prefix="/api/lessons", tags=["lessons"])


@router.get("/")
async def get_lessons(
    db: Session = Depends(get_db),
    user_id: int = Depends(verify_authorization)
) -> List[Dict[str, Any]]:
    """get all available lessons for authenticated user"""
    lessons = db.query(LessonDB).filter(LessonDB.user_id == user_id).order_by(LessonDB.created_at.desc()).all()
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


@router.get("/{lesson_id}")
async def get_lesson(
    lesson_id: int, 
    db: Session = Depends(get_db),
    user_id: int = Depends(verify_authorization)
) -> Dict[str, Any]:
    """get a specific lesson by ID"""
    lesson = db.query(LessonDB).filter(LessonDB.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="lesson not found")
    
    if lesson.user_id != user_id:
        raise HTTPException(status_code=403, detail="access denied")
    
    try:
        states_data = json.loads(lesson.states)  # parse json states
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="invalid lesson states data")
    
    return {
        "id": lesson.id,
        "title": lesson.title,
        "schema_version": lesson.schema_version,
        "estimated_duration_minutes": lesson.estimated_duration_minutes,
        "states": states_data,  # Return parsed states, not JSON string
        "created_at": lesson.created_at.isoformat() if lesson.created_at else None,
        "description": lesson.description,
        "difficulty": lesson.difficulty
    }


@router.delete("/{lesson_id}")
async def delete_lesson(
    lesson_id: int, 
    db: Session = Depends(get_db),
    user_id: int = Depends(verify_authorization)
) -> Dict[str, Any]:
    """delete a lesson by ID"""
    try:
        lesson = db.query(LessonDB).filter(LessonDB.id == lesson_id).first()
        if not lesson:
            raise HTTPException(status_code=404, detail="lesson not found")
        
        if lesson.user_id != user_id:
            raise HTTPException(status_code=403, detail="access denied")
        
        db.delete(lesson)
        db.commit()
        
        return {"message": "lesson deleted successfully"}
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="failed to delete lesson")


@router.post("/generate")
async def generate_lesson(
    request: Dict[str, Any],
    db: Session = Depends(get_db),
    user_id: int = Depends(verify_authorization)
) -> Dict[str, Any]:
    """generate a new lesson using LLM"""
    # auth is handled by dependency
    
    # validate input
    if "text" not in request or len(request["text"]) < 100:
        raise HTTPException(status_code=400, detail="Text content is too short (minimum 100 characters)")
    
    duration = request.get("duration", 30)
    if duration not in [5, 15, 30]:
        raise HTTPException(status_code=400, detail="Duration must be 5, 15, or 30 minutes")
    
    try:
        from services.openai_lesson_generator import OpenAILessonGenerator, StatewiseGenerationError
        
        generator = OpenAILessonGenerator(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            base_url=settings.OPENAI_BASE_URL,
            db_session=db
        )
        
        lesson_id = generator.generate_lesson(
            content=request["text"],
            title=request.get("title", ""),
            description=request.get("description", ""),
            duration_minutes=duration,
            difficulty=request.get("difficulty", "beginner"),
            user_id=user_id
        )
        
        return {
            "lesson_id": lesson_id,
            "message": "lesson generated successfully"
        }
        
    except StatewiseGenerationError as e:
        raise HTTPException(status_code=500, detail=str(e))