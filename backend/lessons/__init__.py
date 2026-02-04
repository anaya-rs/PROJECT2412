"""
Lessons Module - New Architecture
Contains lesson models, FSM, generator, and migration logic.
"""

from .models import (
    Lesson, 
    AuthoredState, 
    ContentState, 
    QuestionState,
    LegacyLesson,
    MigrationRequest,
    MigrationResult
)

from .fsm import LessonFSM, FSMResult, create_fsm_from_lesson, validate_fsm_states
from .generator import LessonGenerator, LessonGenerationError, DURATION_TEMPLATES
from .migration import LegacyMigrator, LessonMigrationError, classify_lesson_schema

__all__ = [
    # Models
    "Lesson",
    "AuthoredState", 
    "ContentState",
    "QuestionState",
    "LegacyLesson",
    "MigrationRequest",
    "MigrationResult",
    
    # FSM
    "LessonFSM",
    "FSMResult", 
    "create_fsm_from_lesson",
    "validate_fsm_states",
    
    # Generator
    "LessonGenerator",
    "LessonGenerationError",
    "DURATION_TEMPLATES",
    
    # Migration
    "LegacyMigrator",
    "LessonMigrationError",
    "classify_lesson_schema"
]
