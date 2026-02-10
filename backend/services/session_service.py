"""
Session Service - High-level session management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from models.lesson import LessonDB
from models.session import LessonSessionDB


class SessionService:
    """
    High-level session management service.
    """
    
    def __init__(self, db_session):
        self.db = db_session
    
    def get_user_sessions(self, user_id: int, lesson_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get sessions for a user, optionally filtered by lesson.
        
        Args:
            user_id: User ID
            lesson_id: Optional lesson ID filter
            
        Returns:
            List of session dictionaries
        """
        query = self.db.query(LessonSessionDB).filter(LessonSessionDB.user_id == user_id)
        
        if lesson_id:
            query = query.filter(LessonSessionDB.lesson_id == lesson_id)
        
        sessions = query.order_by(LessonSessionDB.last_active_at.desc()).all()
        
        return [self._session_to_dict(session) for session in sessions]
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session dictionary or None
        """
        session = self.db.query(LessonSessionDB).filter(
            LessonSessionDB.id == session_id
        ).first()
        
        if not session:
            return None
        
        return self._session_to_dict(session)
    
    def _session_to_dict(self, session: LessonSessionDB) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            "id": session.id,
            "lesson_id": session.lesson_id,
            "user_id": session.user_id,
            "current_index": session.current_index,
            "attempts": session.attempts,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "last_active_at": session.last_active_at.isoformat() if session.last_active_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None
        }