"""
Job Service - Background job management with structured logging and explicit error handling
"""

import uuid
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from models.job import JobDB
from services.lesson_generation import LessonGenerator, LessonGenerationError
from core import get_settings


logger = logging.getLogger(__name__)


class JobService:
    """Service for managing background lesson generation jobs"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.active_jobs = {}  # In-memory job tracking
    
    def create_job(self, user_id: int, payload: Dict[str, Any]) -> str:
        """Create a new background job with structured logging"""
        try:
            job_id = str(uuid.uuid4())
            logger.info(f"Creating new job - job_id: {job_id}, user_id: {user_id}")
            
            job = JobDB(
                id=job_id,
                user_id=user_id,
                status="queued",
                progress=0,
                message="Job queued for processing",
                input_title=payload.get("title"),
                input_description=payload.get("description"),
                file_name=payload.get("fileName"),
                difficulty=payload.get("difficulty"),
                duration=payload.get("duration"),
                question_count=payload.get("questionCount")
            )
            
            self.db.add(job)
            self.db.commit()
            
            logger.info(f"Job saved to database - job_id: {job_id}")
            
            # Start background processing
            logger.info(f"Starting background processing for job - job_id: {job_id}")
            asyncio.create_task(self.process_job_async(job_id, payload))
            
            logger.info(f"Job creation completed - job_id: {job_id}")
            return job_id
            
        except Exception as e:
            error_msg = f"Failed to create job: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status with structured logging"""
        try:
            logger.debug(f"Retrieving job status - job_id: {job_id}")
            
            job = self.db.query(JobDB).filter(JobDB.id == job_id).first()
            if not job:
                logger.warning(f"Job not found - job_id: {job_id}")
                return None
            
            job_dict = job.to_dict()
            logger.debug(f"Job retrieved - job_id: {job_id}, status: {job_dict.get('status')}")
            
            return job_dict
            
        except Exception as e:
            error_msg = f"Failed to retrieve job {job_id}: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    async def process_job_async(self, job_id: str, payload: Dict[str, Any]):
        """Process job in background with comprehensive logging and error handling"""
        lesson_id = None
        
        try:
            logger.info(f"Starting background job processing - job_id: {job_id}")
            
            # Update status to running
            self.update_job_status(job_id, "running", 10, "Processing lesson content...")
            logger.info(f"Job status updated to running - job_id: {job_id}")
            
            # Initialize lesson generator
            settings = get_settings()
            logger.info(f"Initializing lesson generator - model: {settings.OLLAMA_MODEL}")
            
            generator = LessonGenerator(
                ollama_url=settings.OLLAMA_URL,
                model=settings.OLLAMA_MODEL,
                db_session=self.db
            )
            
            # Update progress
            self.update_job_status(job_id, "running", 30, "Generating lesson with AI...")
            logger.info(f"Starting AI generation - job_id: {job_id}")
            
            # Generate lesson
            lesson_id = generator.generate_lesson(
                content=payload["text"],
                title=payload.get("title", "Generated Lesson"),
                description=payload.get("description", ""),
                duration_minutes=payload.get("duration", 30),
                difficulty=payload.get("difficulty", "beginner")
            )
            
            logger.info(f"AI generation completed - job_id: {job_id}, lesson_id: {lesson_id}")
            
            # Mark as completed
            self.update_job_status(
                job_id, 
                "completed", 
                100, 
                "Lesson generation completed successfully",
                lesson_id=lesson_id
            )
            
            logger.info(f"Job completed successfully - job_id: {job_id}, lesson_id: {lesson_id}")
            
        except LessonGenerationError as e:
            error_msg = f"Lesson generation failed: {str(e)}"
            logger.error(f"Job failed due to generation error - job_id: {job_id}, error: {error_msg}")
            self.update_job_status(job_id, "failed", 0, error_msg)
            
        except ValueError as e:
            # Input validation errors
            error_msg = f"Invalid input: {str(e)}"
            logger.error(f"Job failed due to validation error - job_id: {job_id}, error: {error_msg}")
            self.update_job_status(job_id, "failed", 0, error_msg)
            
        except Exception as e:
            # Unexpected errors
            error_msg = f"Unexpected error during processing: {str(e)}"
            logger.error(f"Job failed due to unexpected error - job_id: {job_id}, error: {error_msg}")
            self.update_job_status(job_id, "failed", 0, error_msg)
    
    def update_job_status(self, job_id: str, status: str, progress: int, message: str, lesson_id: int = None):
        """Update job status in database with structured logging"""
        try:
            logger.debug(f"Updating job status - job_id: {job_id}, status: {status}, progress: {progress}")
            
            job = self.db.query(JobDB).filter(JobDB.id == job_id).first()
            if not job:
                logger.error(f"Job not found for status update - job_id: {job_id}")
                return
            
            job.status = status
            job.progress = progress
            job.message = message
            job.updated_at = datetime.utcnow()
            if lesson_id:
                job.lesson_id = lesson_id
            
            self.db.commit()
            logger.debug(f"Job status updated successfully - job_id: {job_id}, status: {status}")
            
        except Exception as e:
            error_msg = f"Failed to update job status {job_id}: {str(e)}"
            logger.error(error_msg)
            # Don't raise here to avoid breaking the job processing flow
