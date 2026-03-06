"""
lesson runtime service 
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
    """service for managing lesson sessions and state transitions with database persistence"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def start_session(self, lesson_id: int, user_id: int) -> str:
        """start a new lesson session with database persistence"""
        session_id = str(uuid.uuid4())
        
        # verify lesson exists
        lesson = self.db.query(LessonDB).filter(LessonDB.id == lesson_id).first()
        if not lesson:
            raise ValueError(f"Lesson {lesson_id} not found")
        
        # create session in database
        session_runtime = LessonSessionRuntimeDB.create_new(session_id, lesson_id, user_id)
        self.db.add(session_runtime)
        self.db.commit()
        
        # log analytics event
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
                "completed": True,
                "status": "completed"
            }
        
        current_state = states_data[current_index]
        
        return {
            "state": current_state,
            "progress": current_index / len(states_data),
            "attempts_left": 3 - session_runtime.attempts,
            "completed": False,
            "status": None
        }
    
    def submit_action(self, session_id: str, user_id: int, action) -> Dict[str, Any]:
        """submit an action and update session state with analytics logging"""
        print(f"🔍 [DEBUG] submit_action called with session_id={session_id}, user_id={user_id}, action={action}")
        
        # session from database
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
                "completed": True,
                "status": "completed"
            }
        
        current_state = states_data[current_index]
        action_type = action.get("type", "unknown")
        
        # Handle different action types
        if action_type == "next":
            # Allow next from content states
            if current_state.get("type") == "question":
                # For question states, check if we have a correct answer or exhausted attempts
                # Check session data for last answer status
                last_answer_status = (session_runtime.session_data or {}).get("last_answer_status")
                
                # Allow next only if status is correct or reveal_answer (attempts exhausted)
                if last_answer_status not in ["correct", "reveal_answer"]:
                    raise ValueError("Cannot advance from question state without correct answer or exhausted attempts")
                else:
                    logger.info(f"Allowing next after {last_answer_status} for session {session_id}")
            
            # Move to next state
            session_runtime.current_index += 1
            session_runtime.attempts = 0  # Reset attempts for new state
            session_runtime.last_active_at = datetime.utcnow()
            
            # Clear the last answer status when advancing
            if session_runtime.session_data and "last_answer_status" in session_runtime.session_data:
                del session_runtime.session_data["last_answer_status"]
            
        elif action_type == "answer":
            # Handle question answers
            if current_state.get("type") != "question":
                raise ValueError("Cannot submit answer to non-question state")
            
            payload = action.get("payload", {})
            selected_option = payload.get("selected_option")
            correct_answers = current_state.get("correct_answers", [])
            
            # Debug logging - COMPREHENSIVE
            logger.info(f"🔍 [ANSWER DEBUG] Action received: {action}")
            logger.info(f"🔍 [ANSWER DEBUG] Payload type: {type(payload)}")
            logger.info(f"🔍 [ANSWER DEBUG] Payload: {payload}")
            logger.info(f"🔍 [ANSWER DEBUG] Selected: {selected_option}")
            logger.info(f"🔍 [ANSWER DEBUG] Selected type: {type(selected_option)}")
            logger.info(f"🔍 [ANSWER DEBUG] Correct answers: {correct_answers}")
            logger.info(f"🔍 [ANSWER DEBUG] Correct answers type: {type(correct_answers)}")
            if correct_answers:
                logger.info(f"🔍 [ANSWER DEBUG] First correct answer type: {type(correct_answers[0])}")
            logger.info(f"🔍 [ANSWER DEBUG] Question options: {current_state.get('options', [])}")
            
            # CRITICAL DEBUG: Log the raw values before any conversion
            logger.info(f"🚨 [ANSWER CRITICAL] session_id: {session_id}")
            logger.info(f"🚨 [ANSWER CRITICAL] current_index: {current_index}")
            logger.info(f"🚨 [ANSWER CRITICAL] selected_option raw: {selected_option}")
            logger.info(f"🚨 [ANSWER CRITICAL] correct_answers raw: {correct_answers}")
            logger.info(f"🚨 [ANSWER CRITICAL] question options with indices:")
            for i, opt in enumerate(current_state.get('options', [])):
                logger.info(f"🚨 [ANSWER CRITICAL]   {i}: {opt}")
            
            # STANDARDIZED COMPARISON: Convert both to integers for index-based validation
            try:
                # Handle both single choice and multiple choice answers
                if isinstance(selected_option, list):
                    selected_indices = [int(x) for x in selected_option if x is not None]
                else:
                    selected_indices = [int(selected_option)] if selected_option is not None else []
                
                # Ensure correct_answers is a list and convert to integers
                if not isinstance(correct_answers, list):
                    logger.error(f"🚨 [ANSWER CRITICAL] correct_answers is not a list: {correct_answers}")
                    correct_answers = []
                correct_indices = [int(ans) for ans in correct_answers if ans is not None]
                
                # Validate indices are within bounds
                max_option_index = len(current_state.get('options', [])) - 1
                if max_option_index >= 0:
                    selected_indices = [idx for idx in selected_indices if 0 <= idx <= max_option_index]
                    correct_indices = [idx for idx in correct_indices if 0 <= idx <= max_option_index]
                else:
                    # No options available, no valid answers
                    selected_indices = []
                    correct_indices = []
                
                # For multiple choice: all selected must be in correct answers AND all correct answers must be selected
                if current_state.get("question_type") == "multiple_choice":
                    is_correct = (set(selected_indices) == set(correct_indices))
                else:
                    # For single choice: selected must be in correct answers
                    is_correct = any(idx in correct_indices for idx in selected_indices)
                
                logger.info(f"🔍 [ANSWER DEBUG] Selected indices: {selected_indices}")
                logger.info(f"🔍 [ANSWER DEBUG] Correct indices: {correct_indices}")
                logger.info(f"🔍 [ANSWER DEBUG] Question type: {current_state.get('question_type')}")
                logger.info(f"🔍 [ANSWER DEBUG] Is correct: {is_correct}")
                
                # ADDITIONAL VALIDATION: Double-check the comparison
                if len(selected_indices) == 1 and len(correct_indices) == 1:
                    direct_comparison = (selected_indices[0] == correct_indices[0])
                    logger.info(f"🔍 [ANSWER DEBUG] Direct comparison: {selected_indices[0]} == {correct_indices[0]} = {direct_comparison}")
                    if direct_comparison != is_correct:
                        logger.error(f"🚨 [ANSWER CRITICAL] Comparison mismatch! direct={direct_comparison}, any_logic={is_correct}")
                        # Use the direct comparison as fallback
                        is_correct = direct_comparison
                
                # FINAL SAFETY CHECK: If no selected indices or no correct indices, mark as incorrect
                if not selected_indices or not correct_indices:
                    logger.warning(f"🔍 [ANSWER DEBUG] No valid indices - selected: {selected_indices}, correct: {correct_indices}")
                    is_correct = False
                
            except Exception as e:
                logger.error(f"� [ANSWER CRITICAL] invalid answer format - selected_option={selected_option} error={e}")
                logger.error(f"� [ANSWER CRITICAL] This is likely a frontend bug sending wrong data type!")
                raise ValueError(f"Invalid answer format received: selected_option={selected_option} (type: {type(selected_option)})")
            
            if is_correct:
                # Correct answer - stay in current state with correct status
                # Store status in session data for next action validation
                if not session_runtime.session_data:
                    session_runtime.session_data = {}
                
                session_runtime.session_data["last_answer_status"] = "correct"
                
                self.db.commit()
                return {
                    "state": current_state,
                    "progress": current_index / len(states_data),
                    "attempts_left": 3 - session_runtime.attempts,
                    "completed": False,
                    "status": "correct",
                    "explanation_visible": True,
                    "correct_answer": int(correct_answers[0]) if correct_answers else None,
                    "feedback": "Correct!"
                }
            else:
                # Wrong answer - increment attempts
                session_runtime.attempts += 1
                session_runtime.last_active_at = datetime.utcnow()
                
                attempts_left = 3 - session_runtime.attempts
                logger.info(f"🔍 [ANSWER DEBUG] Attempts left: {attempts_left}")
                
                if attempts_left > 0:
                    # Return retry response
                    self.db.commit()
                    return {
                        "state": current_state,
                        "progress": current_index / len(states_data),
                        "attempts_left": attempts_left,
                        "completed": False,
                        "status": "retry",
                        "explanation_visible": False,
                        "feedback": "Oops, try again"
                    }
                else:
                    # No attempts left - reveal answer and allow next
                    # Store status in session data for next action validation
                    if not session_runtime.session_data:
                        session_runtime.session_data = {}
                    
                    session_runtime.session_data["last_answer_status"] = "reveal_answer"
                    
                    self.db.commit()
                    return {
                        "state": current_state,
                        "progress": current_index / len(states_data),
                        "attempts_left": 0,
                        "completed": False,
                        "status": "reveal_answer",
                        "explanation_visible": True,
                        "correct_answer": int(correct_answers[0]) if correct_answers else None,
                        "feedback": "No attempts left"
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
                "completed": True,
                "explanation_visible": False,
                "status": "completed"
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
            "completed": False,
            "explanation_visible": False,
            "status": "content"
        }
        print(f"🔍 [DEBUG] Returning normal result: {result}")
        return result
    
    def _get_current_session_state(self, session_id: str, user_id: int) -> Dict[str, Any]:
        """Get the current session state for validation"""
        try:
            # Get session runtime
            session_runtime = self.db.query(LessonSessionRuntimeDB).filter(
                LessonSessionRuntimeDB.session_id == session_id,
                LessonSessionRuntimeDB.user_id == user_id
            ).first()
            
            if not session_runtime:
                return {}
            
            # get lesson states
            lesson = self.db.query(LessonDB).filter(LessonDB.id == session_runtime.lesson_id).first()
            if not lesson:
                return {}
            
            states_data = lesson.states
            current_index = session_runtime.current_index
            
            if current_index >= len(states_data):
                return {"completed": True}
            
            current_state = states_data[current_index]
            
            # determine status based on attempts and state type
            if current_state.get("type") == "question":
                if session_runtime.attempts == 0:
                    return {"status": "pending"}
                elif session_runtime.attempts < 3:
                    return {"status": "retry"}
                else:
                    return {"status": "reveal_answer"}
            else:
                return {"status": "content"}
                
        except Exception as e:
            logger.error(f"Error getting current session state: {e}")
            return {}
    
    def _log_analytics_event(self, session_id: str, lesson_id: int, user_id: int, 
                           state_index: int, event_type: str, payload: Dict[str, Any]):
        """log analytics event for session actions"""
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
            
        except Exception as e:
            logger.error(f"Failed to log analytics event: {e}")
