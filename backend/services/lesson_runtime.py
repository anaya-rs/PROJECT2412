"""
Lesson Runtime Service - Manages lesson sessions and state with database persistence
"""

import logging
from typing import Dict, Any, Optional
import uuid
import json
from datetime import datetime
from sqlalchemy.orm import Session

from models.lesson import LessonDB
from models.session_runtime import LessonSessionRuntimeDB
from models.analytics import AnalyticsEventDB

logger = logging.getLogger(__name__)


class LessonRuntimeService:
    """Service for managing lesson sessions and state transitions with database persistence"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def start_session(self, lesson_id: int, user_id: int) -> str:
        """Start a new lesson session with database persistence"""
        session_id = str(uuid.uuid4())
        
        # Verify lesson exists
        lesson = self.db.query(LessonDB).filter(LessonDB.id == lesson_id).first()
        if not lesson:
            raise ValueError(f"Lesson {lesson_id} not found")
        
        # Create session in database
        session_runtime = LessonSessionRuntimeDB.create_new(session_id, lesson_id, user_id)
        self.db.add(session_runtime)
        self.db.commit()
        
        # Log analytics event
        self._log_analytics_event(session_id, lesson_id, user_id, 0, "start", {})
        
        logger.info(f"Started session {session_id} for lesson {lesson_id}, user {user_id}")
        return session_id
    
    def get_session_state(self, session_id: str, user_id: int) -> Dict[str, Any]:
        """Get current session state with actual lesson content from database"""
        # Get session from database
        session_runtime = self.db.query(LessonSessionRuntimeDB).filter(
            LessonSessionRuntimeDB.id == session_id
        ).first()
        
        if not session_runtime:
            raise ValueError(f"Session {session_id} not found")
        
        if session_runtime.user_id != user_id:
            raise ValueError("Unauthorized access to session")
        
        # Get lesson data
        lesson = self.db.query(LessonDB).filter(LessonDB.id == session_runtime.lesson_id).first()
        if not lesson:
            raise ValueError(f"Lesson {session_runtime.lesson_id} not found")
        
        # Parse lesson states
        try:
            states_data = json.loads(lesson.states)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid lesson states data for lesson {session_runtime.lesson_id}")
        
        # Get current state based on current_index
        current_index = session_runtime.current_index
        if current_index >= len(states_data):
            # Lesson completed
            return {
                "state": None,
                "progress": 1.0,
                "attempts_left": 0,
                "completed": True
            }
        
        current_state = states_data[current_index]
        
        return {
            "state": current_state,
            "progress": current_index / len(states_data),
            "attempts_left": 3 - session_runtime.attempts,
            "completed": False
        }
    
    def submit_action(self, session_id: str, user_id: int, action) -> Dict[str, Any]:
        """Submit an action and update session state with analytics logging"""
        print(f"🔍 [DEBUG] submit_action called with session_id={session_id}, user_id={user_id}, action={action}")
        
        # Get session from database
        session_runtime = self.db.query(LessonSessionRuntimeDB).filter(
            LessonSessionRuntimeDB.id == session_id
        ).first()
        
        if not session_runtime:
            raise ValueError(f"Session {session_id} not found")
        
        if session_runtime.user_id != user_id:
            raise ValueError("Unauthorized access to session")
        
        print(f"🔍 [DEBUG] Session found: current_index={session_runtime.current_index}, attempts={session_runtime.attempts}")
        print(f"🔍 [DEBUG] Session runtime type: {type(session_runtime)}")
        print(f"🔍 [DEBUG] Session runtime dir: {[attr for attr in dir(session_runtime) if not attr.startswith('_')]}")
        
        # Get lesson data
        lesson = self.db.query(LessonDB).filter(LessonDB.id == session_runtime.lesson_id).first()
        if not lesson:
            raise ValueError(f"Lesson {session_runtime.lesson_id} not found")
        
        # Parse lesson states
        try:
            states_data = json.loads(lesson.states)
            print(f"🔍 [DEBUG] Lesson states parsed: {len(states_data)} states")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid lesson states data for lesson {session_runtime.lesson_id}")
        
        # Get current state
        current_index = session_runtime.current_index
        if current_index >= len(states_data):
            return {
                "state": None,
                "progress": 1.0,
                "attempts_left": 0,
                "completed": True
            }
        
        current_state = states_data[current_index]
        action_type = action.get("type", "unknown")
        
        # Handle different action types
        if action_type == "next":
            # Allow next from content states
            if current_state.get("type") == "question":
                # Check if attempts are exhausted (3 wrong answers)
                if session_runtime.attempts < 3:
                    raise ValueError("Cannot advance from question state without answering or exhausting attempts")
                else:
                    # Allow next after 3 wrong attempts
                    logger.info(f"Allowing next after 3 wrong attempts for session {session_id}")
            
            # Move to next state
            session_runtime.current_index += 1
            session_runtime.attempts = 0  # Reset attempts for new state
            session_runtime.last_active_at = datetime.utcnow()
            
        elif action_type == "answer":
            # Handle question answers
            if current_state.get("type") != "question":
                raise ValueError("Cannot submit answer to non-question state")
            
            payload = action.get("payload", {})
            selected_option = payload.get("selected_option")
            correct_answers = current_state.get("correct_answers", [])
            
            # Check if selected option is in correct answers
            is_correct = selected_option in correct_answers
            
            if is_correct:
                # Correct answer - move to next state
                session_runtime.current_index += 1
                session_runtime.attempts = 0
                session_runtime.last_active_at = datetime.utcnow()
            else:
                # Wrong answer - increment attempts
                session_runtime.attempts += 1
                session_runtime.last_active_at = datetime.utcnow()
                
                attempts_left = 3 - session_runtime.attempts
                if attempts_left > 0:
                    # Return retry response
                    self.db.commit()
                    return {
                        "state": current_state,
                        "progress": current_index / len(states_data),
                        "attempts_left": attempts_left,
                        "completed": False,
                        "status": "retry",
                        "message": "Oops, try again"
                    }
                else:
                    # No attempts left - reveal answer and allow next
                    self.db.commit()
                    return {
                        "state": current_state,
                        "progress": current_index / len(states_data),
                        "attempts_left": 0,
                        "completed": False,
                        "status": "reveal_answer",
                        "correct_answer": correct_answers[0] if correct_answers else None,
                        "allow_next": True
                    }
        else:
            raise ValueError(f"Unknown action type: {action_type}")
        
        # Log the action event
        self._log_analytics_event(
            session_id, 
            session_runtime.lesson_id, 
            user_id, 
            current_index, 
            action_type, 
            action.get("payload", {})
        )
        
        # Check if lesson is completed
        if session_runtime.current_index >= len(states_data):
            session_runtime.completed_at = datetime.utcnow()
            self.db.commit()
            
            result = {
                "state": None,
                "progress": 1.0,
                "attempts_left": 0,
                "completed": True
            }
            print(f"🔍 [DEBUG] Returning completed result: {result}")
            return result
        
        # Get next state
        next_state = states_data[session_runtime.current_index]
        self.db.commit()
        
        result = {
            "state": next_state,
            "progress": session_runtime.current_index / len(states_data),
            "attempts_left": 3 - session_runtime.attempts,
            "completed": False
        }
        print(f"🔍 [DEBUG] Returning normal result: {result}")
        return result
    
    def _log_analytics_event(self, session_id: str, lesson_id: int, user_id: int, 
                           state_index: int, event_type: str, payload: Dict[str, Any]):
        """Log analytics event for session actions"""
        try:
            import json
            import uuid
            
            analytics_event = AnalyticsEventDB(
                id=str(uuid.uuid4()),
                session_id=session_id,
                lesson_id=lesson_id,
                user_id=user_id,
                state_index=state_index,
                event_type=event_type,
                payload=json.dumps(payload) if payload else "{}"
            )
            
            self.db.add(analytics_event)
            # Note: Don't commit here to avoid interfering with main transaction
            # The calling method should handle the commit
            
        except Exception as e:
            logger.error(f"Failed to log analytics event: {e}")
            # Don't raise - analytics failures shouldn't break the main flow
