"""
Domain Module - Pure business logic, no external dependencies
"""

from .state import (
    BaseState, ContentState, QuestionState, EndNotesState,
    AuthoredState, DomainEvent
)
from .lesson import Lesson
from .fsm import (
    FSMResult, UserAction, LessonSession, 
    step
)
from .validation import (
    validate_duration_constraints,
    validate_lesson_structure,
    DURATION_TEMPLATES
)

__all__ = [
    # State
    "BaseState",
    "ContentState", 
    "QuestionState",
    "EndNotesState",
    "AuthoredState",
    "DomainEvent",
    
    # Lesson
    "Lesson",
    
    # FSM
    "FSMResult",
    "UserAction",
    "LessonSession", 
    "step",
    
    # Validation
    "validate_duration_constraints",
    "validate_lesson_structure",
    "DURATION_TEMPLATES"
]
