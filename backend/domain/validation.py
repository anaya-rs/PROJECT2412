"""
Domain Validation - Pure validation logic, no side effects
"""

from typing import List
from .state import AuthoredState
from .lesson import Lesson


# Duration templates - code-only rules
DURATION_RULES = {
    5:  {"min_questions": 1, "max_questions": 2, "min_content": 1},
    30: {"min_questions": 3, "max_questions": 5, "min_content": 3},
    60: {"min_questions": 5, "max_questions": 8, "min_content": 5},
}


def validate_duration_constraints(states: List[AuthoredState], duration_minutes: int) -> bool:
    """
    Validate that states match duration constraints.
    
    Args:
        states: List of lesson states
        duration_minutes: Target duration
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If constraints are not met
    """
    if duration_minutes not in DURATION_RULES:
        raise ValueError(f"Invalid duration: {duration_minutes}")
    
    template = DURATION_RULES[duration_minutes]
    
    question_count = sum(1 for s in states if s.type == "question")
    content_count = sum(1 for s in states if s.type == "content")
    
    if question_count < template["min_questions"]:
        raise ValueError(f"Duration {duration_minutes}min requires at least {template['min_questions']} questions")
    
    if question_count > template["max_questions"]:
        raise ValueError(f"Duration {duration_minutes}min allows at most {template['max_questions']} questions")
    
    if content_count < template["min_content"]:
        raise ValueError(f"Duration {duration_minutes}min requires at least {template['min_content']} content blocks")
    
    return True


def validate_lesson_structure(lesson: Lesson) -> bool:
    """
    Validate lesson structure and business rules.
    
    Args:
        lesson: Lesson to validate
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If validation fails
    """
    # Basic structure validation (handled by Pydantic)
    if not lesson.states:
        raise ValueError("Lesson must have states")
    
    # Business rules
    if len(lesson.states) < 2:
        raise ValueError("Lesson must have at least 2 states")
    
    # Check first state is content
    if lesson.states[0].type != "content":
        raise ValueError("First state must be content")
    
    # No consecutive questions
    for i in range(len(lesson.states) - 1):
        if lesson.states[i].type == lesson.states[i + 1].type == "question":
            raise ValueError("Two questions cannot appear consecutively")
    
    # Duration constraints
    validate_duration_constraints(lesson.states, lesson.estimated_duration_minutes)
    
    return True
