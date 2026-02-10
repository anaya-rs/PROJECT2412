"""
Domain FSM - Pure deterministic logic, no side effects
"""

from typing import Dict, Any, List, Literal
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel

from .lesson import Lesson
from .state import AuthoredState, ContentState, QuestionState, DomainEvent


class FSMResult(BaseModel):
    """Result of FSM step - pure data, no persistence"""
    next_index: int
    next_attempts: int
    completed: bool
    events: List[DomainEvent]


class UserAction(BaseModel):
    """User action input"""
    type: Literal["next", "answer"]
    payload: dict | None = None


class LessonSession(BaseModel):
    """Runtime session state - pure domain model"""
    id: str  # UUID
    lesson_id: int
    user_id: int
    current_index: int = 0
    attempts: int = 0
    started_at: datetime
    last_active_at: datetime
    completed_at: datetime | None = None


def step(
    lesson: Lesson,
    session: LessonSession,
    action: UserAction
) -> FSMResult:
    """
    Deterministic FSM step function.
    
    Args:
        lesson: Immutable lesson artifact
        session: Current runtime state
        action: User action to process
        
    Returns:
        FSMResult with next state and events
    """
    events: List[DomainEvent] = []
    current_state = lesson.states[session.current_index]
    
    # Handle different action types
    if action.type == "next":
        if not isinstance(current_state, ContentState):
            raise ValueError("Cannot 'next' from question state")
        
        # Content always advances
        events.append(DomainEvent(
            event_type="advance",
            payload={"reason": "content_complete"}
        ))
        
        next_index = session.current_index + 1
        next_attempts = 0
        
        # Check if lesson completed
        if next_index >= len(lesson.states):
            events.append(DomainEvent(
                event_type="complete",
                payload={"total_states": len(lesson.states)}
            ))
            return FSMResult(
                next_index=next_index,
                next_attempts=next_attempts,
                completed=True,
                events=events
            )
        
        # Enter next state
        events.append(DomainEvent(
            event_type="enter",
            payload={"state_id": lesson.states[next_index].id}
        ))
        
        return FSMResult(
            next_index=next_index,
            next_attempts=next_attempts,
            completed=False,
            events=events
        )
    
    elif action.type == "answer":
        if not isinstance(current_state, QuestionState):
            raise ValueError("Cannot 'answer' content state")
        
        user_answer = action.payload.get("answer") if action.payload else None
        is_correct = _check_answer(current_state, user_answer)
        
        # Log answer event
        events.append(DomainEvent(
            event_type="answer",
            payload={
                "state_id": current_state.id,
                "correct": is_correct,
                "attempt": session.attempts + 1,
                "user_answer": user_answer
            }
        ))
        
        if is_correct:
            # Correct answer - advance immediately
            events.append(DomainEvent(
                event_type="advance",
                payload={"reason": "correct"}
            ))
            
            next_index = session.current_index + 1
            next_attempts = 0
            
            # Check if lesson completed
            if next_index >= len(lesson.states):
                events.append(DomainEvent(
                    event_type="complete",
                    payload={"total_states": len(lesson.states)}
                ))
                return FSMResult(
                    next_index=next_index,
                    next_attempts=next_attempts,
                    completed=True,
                    events=events
                )
            
            # Enter next state
            events.append(DomainEvent(
                event_type="enter",
                payload={"state_id": lesson.states[next_index].id}
            ))
            
            return FSMResult(
                next_index=next_index,
                next_attempts=next_attempts,
                completed=False,
                events=events
            )
        
        else:
            # Wrong answer logic
            if session.attempts == 0:
                # First wrong attempt - retry
                events.append(DomainEvent(
                    event_type="retry",
                    payload={"attempt": 1}
                ))
                
                return FSMResult(
                    next_index=session.current_index,
                    next_attempts=session.attempts + 1,
                    completed=False,
                    events=events
                )
            
            else:
                # Second wrong attempt - force advance
                events.append(DomainEvent(
                    event_type="advance",
                    payload={"reason": "wrong_final"}
                ))
                
                next_index = session.current_index + 1
                next_attempts = 0
                
                # Check if lesson completed
                if next_index >= len(lesson.states):
                    events.append(DomainEvent(
                        event_type="complete",
                        payload={"total_states": len(lesson.states)}
                    ))
                    return FSMResult(
                        next_index=next_index,
                        next_attempts=next_attempts,
                        completed=True,
                        events=events
                    )
                
                # Enter next state
                events.append(DomainEvent(
                    event_type="enter",
                    payload={"state_id": lesson.states[next_index].id}
                ))
                
                return FSMResult(
                    next_index=next_index,
                    next_attempts=next_attempts,
                    completed=False,
                    events=events
                )
    
    else:
        raise ValueError(f"Unknown action type: {action.type}")


def _check_answer(question: QuestionState, user_answer: Any) -> bool:
    """Check if user answer is correct"""
    if question.question_format == "mcq":
        return isinstance(user_answer, int) and user_answer == question.correct_answer
    elif question.question_format == "short_answer":
        return isinstance(user_answer, str) and user_answer.strip().lower() == question.correct_answer.strip().lower()
    else:
        return False
