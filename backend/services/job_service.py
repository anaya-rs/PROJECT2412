"""
v 1.1 Job Service - Background job management with structured logging and explicit error handling
"""

import uuid
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from core.config import settings
from models.job import JobDB
from services.openai_lesson_generator import OpenAILessonGenerator, StatewiseGenerationError

logger = logging.getLogger(__name__)


class JobService:
    """service for managing background lesson generation jobs"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.active_jobs = {}  # In-memory job tracking
    
    def create_job(self, user_id: int, payload: Dict[str, Any]) -> str:
        """create a new background job with structured logging"""
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
            
            # Return job_id immediately - background processing will be handled by FastAPI
            logger.info(f"Job creation completed - job_id: {job_id}")
            return job_id
            
        except Exception as e:
            error_msg = f"Failed to create job: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """get job status with structured logging"""
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
    
    async def process_job_async(self, job_id: str, payload: Dict[str, Any], user_id: int):
        """process job in background with comprehensive logging and error handling"""
        lesson_id = None
        
        # Create new database session for background task
        from core.db import get_db_session
        db = get_db_session()
        
        try:
            logger.info(f"Starting background job processing - job_id: {job_id}")
            
            # update status to running
            self.update_job_status(db, job_id, "running", 10, "Processing lesson content...")
            logger.info(f"Job status updated to running - job_id: {job_id}")
            
            # initialize lesson generator
            logger.info(f"Initializing OpenAI lesson generator - model: {settings.OPENAI_MODEL}")
            
            generator = OpenAILessonGenerator(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL,
                base_url=settings.OPENAI_BASE_URL,
                db_session=db
            )
            
            # update progress
            self.update_job_status(db, job_id, "running", 30, "Generating lesson with AI...")
            logger.info(f"Starting AI generation - job_id: {job_id}")
            
            # generate lesson
            lesson_id = generator.generate_lesson(
                content=payload["text"],
                title=payload.get("title", "Generated Lesson"),
                description=payload.get("description", ""),
                duration_minutes=payload.get("duration", 30),
                difficulty=payload.get("difficulty", "beginner"),
                user_id=user_id
            )
            
            logger.info(f"AI generation completed - job_id: {job_id}, lesson_id: {lesson_id}")
            
            # mark as completed 
            self.update_job_status(
                db, 
                job_id, 
                "completed", 
                100, 
                "Lesson generation completed successfully",
                lesson_id=lesson_id
            )
            
            logger.info(f"Job completed successfully - job_id: {job_id}, lesson_id: {lesson_id}")
            
        except StatewiseGenerationError as e:
            error_msg = f"Lesson generation failed: {str(e)}"
            logger.error(f"Job failed due to generation error - job_id: {job_id}, error: {error_msg}")
            self.update_job_status(db, job_id, "failed", 0, error_msg)
            
        except ValueError as e:
            # input validation errors
            error_msg = f"Invalid input: {str(e)}"
            logger.error(f"Job failed due to validation error - job_id: {job_id}, error: {error_msg}")
            self.update_job_status(db, job_id, "failed", 0, error_msg)
            
        except Exception as e:
            # unexpected errors
            error_msg = f"Unexpected error during processing: {str(e)}"
            logger.error(f"Job failed due to unexpected error - job_id: {job_id}, error: {error_msg}")
            self.update_job_status(db, job_id, "failed", 0, error_msg)
        finally:
            # Always close the database session
            db.close()
    
    def update_job_status(self, db, job_id: str, status: str, progress: int, message: str, lesson_id: int = None):
        """update job status in database with structured logging"""
        try:
            logger.debug(f"Updating job status - job_id: {job_id}, status: {status}, progress: {progress}")
            
            job = db.query(JobDB).filter(JobDB.id == job_id).first()
            if not job:
                logger.error(f"Job not found for status update - job_id: {job_id}")
                return
            
            job.status = status
            job.progress = progress
            job.message = message
            job.updated_at = datetime.utcnow()
            if lesson_id:
                job.lesson_id = lesson_id
            
            db.commit()
            logger.debug(f"Job status updated successfully - job_id: {job_id}, status: {status}")
            
        except Exception as e:
            error_msg = f"Failed to update job status {job_id}: {str(e)}"
            logger.error(error_msg)
            # don't raise here to avoid breaking the job processing flow
