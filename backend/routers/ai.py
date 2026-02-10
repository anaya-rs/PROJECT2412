"""
AI Router - Mock AI endpoints for compatibility
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/generate-lesson")
async def generate_lesson_direct(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Direct lesson generation (simplified version)
    This is a mock implementation - in production would call actual AI service
    """
    text = payload.get("text", "")
    if not text or len(text) < 100:
        raise HTTPException(status_code=400, detail="Text content is too short (minimum 100 characters)")
    
    # Mock lesson generation
    return {
        "success": True,
        "lesson": {
            "id": 1,
            "title": payload.get("title", "Generated Lesson"),
            "schema_version": "1.0",
            "estimated_duration_minutes": payload.get("duration", 30),
            "states": [
                {
                    "id": "c1",
                    "type": "content",
                    "text": "Generated content based on your input"
                },
                {
                    "id": "q1",
                    "type": "question",
                    "question_format": "mcq",
                    "prompt": "What is the main topic of this content?",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": 0,
                    "explanation": "This is the correct explanation"
                }
            ],
            "created_at": datetime.utcnow().isoformat()
        }
    }


@router.post("/jobs")
async def create_ai_job(payload: Dict[str, Any]) -> Dict[str, str]:
    """
    Create an AI job (mock implementation)
    """
    job_id = str(uuid.uuid4())
    return {"jobId": job_id}


@router.get("/jobs/{job_id}")
async def get_ai_job(job_id: str) -> Dict[str, Any]:
    """
    Get AI job status (mock implementation)
    """
    return {
        "id": job_id,
        "userId": 1,
        "status": "completed",
        "progress": 100,
        "message": "Lesson generation completed",
        "lessonId": 1,
        "inputTitle": "Generated Lesson",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
