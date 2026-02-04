"""
FSM Executor - Runtime Engine (Deterministic)
This is the only place branching exists.
"""

from typing import Dict, Any, List
from .models import AuthoredState, ContentState, QuestionState


class FSMResult:
    def __init__(self, feedback: str, advance: bool, state: AuthoredState = None):
        self.feedback = feedback
        self.advance = advance
        self.state = state


class LessonFSM:
    """
    Deterministic Finite State Machine for lesson execution.
    
    Key invariants:
    - No infinite loops
    - Max 2 attempts per question
    - LLM never controls flow
    - FSM is unit-testable in isolation
    """
    
    def __init__(self, states: List[AuthoredState]):
        if not states:
            raise ValueError("Lesson must have at least one state")
        
        self.states = states
        self.index = 0
        self.attempts = 0
        self._events = []  # For analytics
    
    @property
    def current_state(self) -> AuthoredState:
        """Get the current state"""
        if self.index >= len(self.states):
            raise ValueError("Lesson is finished")
        return self.states[self.index]
    
    @property
    def is_finished(self) -> bool:
        """Check if lesson is complete"""
        return self.index >= len(self.states)
    
    @property
    def progress(self) -> float:
        """Get progress percentage (0-100)"""
        if len(self.states) == 0:
            return 0.0
        return min(100.0, (self.index / len(self.states)) * 100)
    
    def submit_answer(self, is_correct: bool) -> FSMResult:
        """
        Submit an answer for the current question state.
        
        Returns:
            FSMResult with feedback and whether to advance
        """
        if self.is_finished:
            raise ValueError("Cannot submit answer to finished lesson")
        
        current = self.current_state
        
        if not isinstance(current, QuestionState):
            raise ValueError("Cannot submit answer to content state")
        
        # Log the answer event
        self._log_event("answer", {
            "state_id": current.id,
            "correct": is_correct,
            "attempt": self.attempts + 1
        })
        
        if is_correct:
            # Correct answer - advance immediately
            self._log_event("advance", {"reason": "correct"})
            result = FSMResult(
                feedback="correct",
                advance=True,
                state=current
            )
            self._advance_state()
            return result
        
        # Wrong answer logic
        if self.attempts == 0:
            # First wrong attempt - show explanation and retry
            self.attempts += 1
            self._log_event("retry", {"attempt": 1})
            return FSMResult(
                feedback="wrong_retry",
                advance=False,
                state=current
            )
        
        # Second wrong attempt - show explanation and force advance
        self._log_event("advance", {"reason": "wrong_final"})
        result = FSMResult(
            feedback="wrong_final",
            advance=True,
            state=current
        )
        self._advance_state()
        return result
    
    def advance_content(self) -> FSMResult:
        """
        Advance from a content state.
        
        Returns:
            FSMResult for content advancement
        """
        if self.is_finished:
            raise ValueError("Cannot advance finished lesson")
        
        current = self.current_state
        
        if not isinstance(current, ContentState):
            raise ValueError("Cannot advance from question state")
        
        self._log_event("advance", {"reason": "content_complete"})
        result = FSMResult(
            feedback="content_complete",
            advance=True,
            state=current
        )
        self._advance_state()
        return result
    
    def get_events(self) -> List[Dict[str, Any]]:
        """Get all logged events for analytics"""
        return self._events.copy()
    
    def _advance_state(self):
        """Internal method to advance to next state"""
        self.index += 1
        self.attempts = 0  # Reset attempts on state change
        
        if not self.is_finished:
            self._log_event("enter", {"state_id": self.states[self.index].id})
        else:
            self._log_event("complete", {
                "total_states": len(self.states),
                "final_progress": 100.0
            })
    
    def _log_event(self, event_type: str, payload: Dict[str, Any]):
        """Log an event for analytics"""
        self._events.append({
            "event_type": event_type,
            "payload": payload
        })


# ---------- Utility Functions ----------

def create_fsm_from_lesson(lesson_data: dict) -> LessonFSM:
    """
    Create FSM from lesson data with validation.
    
    Args:
        lesson_data: Dictionary containing lesson with states
        
    Returns:
        LessonFSM instance
        
    Raises:
        ValueError: If lesson data is invalid
    """
    from .models import Lesson
    
    # Validate lesson structure
    lesson = Lesson.parse_obj(lesson_data)
    
    return LessonFSM(lesson.states)


def validate_fsm_states(states: List[AuthoredState]) -> bool:
    """
    Validate that states are suitable for FSM execution.
    
    Args:
        states: List of authored states
        
    Returns:
        True if valid, raises ValueError if invalid
    """
    if not states:
        raise ValueError("No states provided")
    
    # Check that first state is content
    if states[0].type != "content":
        raise ValueError("First state must be content")
    
    # Check for consecutive questions (handled by model validation)
    # Check that last state can be content or question
    # Additional FSM-specific validations can be added here
    
    return True
