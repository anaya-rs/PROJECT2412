"""
domain validation
"""

from typing import List
from .state import AuthoredState
from .lesson import Lesson


# fixed duration templates - new requirements state-wise generation
DURATION_TEMPLATES = {
    5: {
        "total_pages": 6,  # 3 content + 2 question + 1 end_notes
        "content_pages": 3, 
        "question_pages": 2, 
        "end_notes_pages": 1,
        "structure": ["content", "question", "content", "question", "content", "end_notes"]
    },
    15: {
        "total_pages": 10,  # 5 content + 4 question + 1 end_notes
        "content_pages": 5, 
        "question_pages": 4, 
        "end_notes_pages": 1,
        "structure": ["content", "question", "content", "question", "content", "question", "content", "question", "content", "end_notes"]
    },
    30: {
        "total_pages": 14,  # 8 content + 5 question + 1 end_notes
        "content_pages": 8, 
        "question_pages": 5, 
        "end_notes_pages": 1,
        "structure": ["content", "question", "content", "question", "content", "question", "content", "question", "content", "question", "content", "question", "content", "end_notes"]
    }
}


def validate_duration_constraints(states: List[AuthoredState], duration_minutes: int) -> bool:
    """
    Validate lesson duration constraints using exact page counts
    """
    template = DURATION_TEMPLATES.get(duration_minutes)
    if not template:
        raise ValueError(f"Invalid duration: {duration_minutes}")
    
    required_count = template['total_pages']
    
    if len(states) != required_count:
        raise ValueError(f"Duration {duration_minutes}min requires exactly {required_count} states, got {len(states)}")
       
    # validate first state is content
    if states[0].type != "content":
        raise ValueError("First state must be content")
    
    # validate no consecutive questions
    for i in range(len(states) - 1):
        if states[i].type == states[i + 1].type == "question":
            raise ValueError("No consecutive questions allowed")
    
    # validate all questions have required fields
    for i, state in enumerate(states):
        if state.type == "question":
            if not hasattr(state, 'prompt') or not state.prompt:
                raise ValueError(f"Question at position {i} is missing prompt")
            if not hasattr(state, 'explanation') or not state.explanation:
                raise ValueError(f"Question at position {i} is missing explanation")
            if state.question_type in ["single_choice", "multiple_choice"]:
                if not hasattr(state, 'options') or not state.options or len(state.options) < 2:
                    raise ValueError(f"Question at position {i} requires at least 2 options")
                if not hasattr(state, 'correct_answers') or not state.correct_answers:
                    raise ValueError(f"Question at position {i} requires correct_answers list")
                # validate correct answer indices
                for idx in state.correct_answers:
                    if idx < 0 or idx >= len(state.options):
                        raise ValueError(f"Question at position {i} correct_answer index {idx} out of bounds")
    

    # validate no empty content blocks
    for i, state in enumerate(states):
        if state.type == "content":
            if not hasattr(state, 'text') or not state.text.strip():
                raise ValueError(f"Content page at position {i} has empty text")
    
    return True


def validate_lesson_structure(lesson: Lesson) -> bool:
    """
    validate lesson structure against fixed templates.
    
    Args:
        lesson: Lesson to validate
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If validation fails
    """
    # basic structure validation (handled by Pydantic)
    if not lesson.states:
        raise ValueError("Lesson must have states")
    
    # check first state is content
    if lesson.states[0].type != "content":
        raise ValueError("First state must be content")
    
    # apply fixed template validation
    validate_duration_constraints(lesson.states, lesson.estimated_duration_minutes)
    
    return True
