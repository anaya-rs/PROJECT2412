"""
AI Router
"""

import logging
import asyncio
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any
from sqlalchemy.orm import Session
from services.job_service import JobService
from core.dependencies import get_db, verify_authorization


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/jobs")
async def create_ai_job(
    payload: Dict[str, Any], 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db), 
    user_id: int = Depends(verify_authorization)
):
    """
    create an AI job and start background processing with explicit error handling
    """
    try:
        logger.info(f"Lesson generation request received - user_id: {user_id}")
        
        # Extract and validate input
        text = payload.get("text", "")
        duration = payload.get("duration", 30)
        title = payload.get("title")
        description = payload.get("description")
        difficulty = payload.get("difficulty", "beginner")
        
        logger.info(f"Request details - text_length: {len(text)}, duration: {duration}, difficulty: {difficulty}")
        
        # Input validation with explicit errors
        if not text or len(text) < 100:
            error_msg = f"Text content is too short (minimum 100 characters, got {len(text)})"
            logger.error(f"Input validation failed: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        if duration not in [5, 15, 30]:
            error_msg = "Only 5, 15, and 30 minute lessons are supported."
            logger.error(f"Duration validation failed: {error_msg} Got: {duration}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        logger.info("Input validation passed, creating job")
        
        # Create job
        job_service = JobService(db)
        job_id = job_service.create_job(user_id, payload)
        
        logger.info(f"Job created successfully - job_id: {job_id}")
        
        # Add background task to process the job
        background_tasks.add_task(job_service.process_job_async, job_id, payload, user_id)
        
        return {
            "jobId": job_id,
            "status": "queued",
            "message": "Lesson generation queued successfully"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        # Catch any unexpected errors and surface them explicitly
        error_msg = f"Unexpected error creating job: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/jobs/{job_id}")
async def get_ai_job(job_id: str, db: Session = Depends(get_db), user_id: int = Depends(verify_authorization)):
    """
    get AI job status with explicit error handling
    """
    try:
        logger.info(f"Job status request - job_id: {job_id}, user_id: {user_id}")
        
        job_service = JobService(db)
        job = job_service.get_job(job_id)
        
        if not job:
            error_msg = f"Job not found: {job_id}"
            logger.error(error_msg)
            raise HTTPException(status_code=404, detail=error_msg)
        
        # verify user owns this job
        if job["userId"] != user_id:
            error_msg = "Access denied: job belongs to different user"
            logger.error(f"Access denied - job_user: {job['userId']}, request_user: {user_id}")
            raise HTTPException(status_code=403, detail=error_msg)
        
        logger.info(f"Job status retrieved - job_id: {job_id}, status: {job['status']}")
        
        # return proper response contract
        if job["status"] == "completed":
            return {
                "jobId": job["id"],
                "status": job["status"],
                "progress": job["progress"],
                "message": job["message"],
                "lesson_id": job["lessonId"],
                "duration": job["duration"],
                "pages_created": "Available in lesson data"
            }
        elif job["status"] == "failed":
            return {
                "jobId": job["id"],
                "status": job["status"],
                "progress": job["progress"],
                "error": job["message"],
                "stage": "generation_failed"
            }
        else:
            # running or queued
            return {
                "jobId": job["id"],
                "status": job["status"],
                "progress": job["progress"],
                "message": job["message"]
            }
        
    except HTTPException:
        # re-raise HTTP exceptions (not found, access denied)
        raise
    except Exception as e:
        # catch any unexpected errors and surface them explicitly
        error_msg = f"Unexpected error retrieving job: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)