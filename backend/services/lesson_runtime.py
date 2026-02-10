"""
Lesson Runtime Service - Core runtime orchestration
"""

from typing import Dict, Any
from datetime import datetime

from domain.lesson import Lesson
from domain.fsm import UserAction, FSMResult, step
from domain.state import AuthoredState
from models.lesson import LessonDB
from models.session import LessonSessionDB
from models.analytics import AnalyticsEventDB


class LessonRuntimeService:
    """
    Core runtime service - orchestrates FSM and persistence.
    
    This is the single authority for lesson execution logic.
    """
    
    def __init__(self, db_session):
        self.db = db_session
    
    def start_session(self, lesson_id: int, user_id: int) -> str:
        """
        Start a new lesson session.
        
        Args:
            lesson_id: Lesson ID
            user_id: User ID
            
        Returns:
            Session ID (UUID)
        """
        import uuid
        
        # Load lesson
        lesson_db = self.db.query(LessonDB).filter(LessonDB.id == lesson_id).first()
        if not lesson_db:
            raise ValueError(f"Lesson {lesson_id} not found")
        
        lesson = lesson_db.to_domain()
        
        # Create session
        session_id = str(uuid.uuid4())
        from domain.fsm import LessonSession
        
        session_domain = LessonSession(
            id=session_id,
            lesson_id=lesson_id,
            user_id=user_id,
            current_index=0,
            attempts=0,
            started_at=datetime.utcnow(),
            last_active_at=datetime.utcnow()
        )
        
        session_db = LessonSessionDB.from_domain(session_domain)
        self.db.add(session_db)
        self.db.commit()
        
        # Create initial 'enter' event for state 0
        from domain.state import DomainEvent
        
        enter_event = DomainEvent(
            event_type="enter",
            payload={"state_id": lesson.states[0].id}
        )
        
        self._persist_event(enter_event, session_id, lesson_id, user_id, 0)
        
        return session_id
    
    def submit_action(self, session_id: str, user_id: int, action: UserAction) -> Dict[str, Any]:
        """
        Submit user action and process through FSM.
        
        Args:
            session_id: Session ID
            user_id: User ID
            action: User action
            
        Returns:
            Result dictionary with next state info
        """
        # Load session and lesson
        session_db = self.db.query(LessonSessionDB).filter(
            LessonSessionDB.id == session_id
        ).first()
        
        if not session_db:
            raise ValueError(f"Session {session_id} not found")
        
        if session_db.user_id != user_id:
            raise ValueError("Access denied")
        
        lesson_db = self.db.query(LessonDB).filter(
            LessonDB.id == session_db.lesson_id
        ).first()
        
        if not lesson_db:
            raise ValueError(f"Lesson {session_db.lesson_id} not found")
        
        # Convert to domain models
        session = session_db.to_domain()
        lesson = lesson_db.to_domain()
        
        # Check if session is already completed
        if session.completed_at:
            raise ValueError("Session already completed")
        
        # Process action through FSM
        result = step(lesson, session, action)
        
        # Update session state in database
        session_db.current_index = result.next_index
        session_db.attempts = result.next_attempts
        session_db.last_active_at = datetime.utcnow()
        
        if result.completed:
            session_db.completed_at = datetime.utcnow()
        
        self.db.commit()
        
        # Update domain object with new values
        session.current_index = result.next_index
        session.attempts = result.next_attempts
        session.last_active_at = datetime.utcnow()
        
        if result.completed:
            session.completed_at = datetime.utcnow()
        
        # Persist analytics events
        for i, event in enumerate(result.events):
            self._persist_event(event, session_id, lesson.id, user_id, session.current_index)
        
        # Return response for frontend
        return self._build_session_response(lesson, session, result)
    
    def get_session_state(self, session_id: str, user_id: int) -> Dict[str, Any]:
        """
        Get current session state for resuming.
        
        Args:
            session_id: Session ID
            user_id: User ID
            
        Returns:
            Session state dictionary
        """
        # Load session and lesson
        session_db = self.db.query(LessonSessionDB).filter(
            LessonSessionDB.id == session_id
        ).first()
        
        if not session_db:
            raise ValueError(f"Session {session_id} not found")
        
        if session_db.user_id != user_id:
            raise ValueError("Access denied")
        
        lesson_db = self.db.query(LessonDB).filter(
            LessonDB.id == session_db.lesson_id
        ).first()
        
        if not lesson_db:
            raise ValueError(f"Lesson {session_db.lesson_id} not found")
        
        # Convert to domain models
        session = session_db.to_domain()
        lesson = lesson_db.to_domain()
        
        return self._build_session_response(lesson, session, None)
    
    def _persist_event(self, event, session_id: str, lesson_id: int, user_id: int, state_index: int):
        """Persist analytics event to database"""
        event_db = AnalyticsEventDB.from_domain_event(event, session_id, lesson_id, user_id)
        event_db.state_index = state_index
        self.db.add(event_db)
        self.db.commit()
    
    def _build_session_response(self, lesson: Lesson, session, fsm_result: FSMResult = None) -> Dict[str, Any]:
        """Build session state response for frontend"""
        # Check if lesson is completed
        if session.current_index >= len(lesson.states):
            return {
                "state": None,
                "progress": 1.0,
                "attempts_left": 0,
                "completed": True
            }
        
        current_state = lesson.states[session.current_index]
        progress = session.current_index / len(lesson.states)
        attempts_left = 2 - session.attempts  # Max 2 attempts per question
        
        return {
            "state": current_state.model_dump(),
            "progress": progress,
            "attempts_left": max(0, attempts_left),
            "completed": session.completed_at is not None
        }
