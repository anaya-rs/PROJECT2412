"""
Domain Validation - Pure validation logic, no side effects
"""

from typing import List
from .state import AuthoredState
from .lesson import Lesson


# Fixed duration templates - code-only rules
DURATION_TEMPLATES = {
    5: {
        "total_pages": 5,
        "content_pages": 2, 
        "question_pages": 2, 
        "end_notes_pages": 1,
        "structure": ["content", "question", "content", "question", "end_notes"]
    },
    15: {
        "total_pages": 9,
        "content_pages": 4, 
        "question_pages": 4, 
        "end_notes_pages": 1,
        "structure": ["content", "question", "content", "question", "content", "question", "content", "question", "end_notes"]
    },
    30: {
        "total_pages": 13,
        "content_pages": 6, 
        "question_pages": 6, 
        "end_notes_pages": 1,
        "structure": ["content", "question", "content", "question", "content", "question", "content", "question", "content", "question", "content", "question", "end_notes"]
    }
}


def validate_duration_constraints(states: List[AuthoredState], duration_minutes: int) -> bool:
    """
    Validate that states match fixed duration templates exactly.
    
    Args:
        states: List of lesson states
        duration_minutes: Target duration
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If constraints are not met
    """
    if duration_minutes not in DURATION_TEMPLATES:
        raise ValueError(f"Only 5, 15, and 30 minute lessons are supported. Got {duration_minutes}.")
    
    template = DURATION_TEMPLATES[duration_minutes]
    
    # Count page types
    content_count = sum(1 for s in states if s.type == "content")
    question_count = sum(1 for s in states if s.type == "question")
    end_notes_count = sum(1 for s in states if s.type == "end_notes")
    
    # Validate exact counts
    if len(states) != template["total_pages"]:
        raise ValueError(f"Duration {duration_minutes}min requires exactly {template['total_pages']} pages, got {len(states)}")
    
    if content_count != template["content_pages"]:
        raise ValueError(f"Duration {duration_minutes}min requires exactly {template['content_pages']} content pages, got {content_count}")
    
    if question_count != template["question_pages"]:
        raise ValueError(f"Duration {duration_minutes}min requires exactly {template['question_pages']} question pages, got {question_count}")
    
    if end_notes_count != template["end_notes_pages"]:
        raise ValueError(f"Duration {duration_minutes}min requires exactly {template['end_notes_pages']} end_notes page, got {end_notes_count}")
    
    # Validate structure matches template exactly
    expected_structure = template["structure"]
    actual_structure = [s.type for s in states]
    
    if actual_structure != expected_structure:
        raise ValueError(f"Lesson structure does not match template. Expected: {expected_structure}, Got: {actual_structure}")
    
    # Validate END_NOTES is last
    if states[-1].type != "end_notes":
        raise ValueError("END_NOTES page must be the last page in the lesson")
    
    # Validate no consecutive questions
    for i in range(len(states) - 1):
        if states[i].type == states[i + 1].type == "question":
            raise ValueError("Two questions cannot appear consecutively")
    
    # Validate all questions have required fields
    for i, state in enumerate(states):
        if state.type == "question":
            if not hasattr(state, 'prompt') or not state.prompt:
                raise ValueError(f"Question at position {i} is missing prompt")
            if not hasattr(state, 'explanation') or not state.explanation:
                raise ValueError(f"Question at position {i} is missing explanation")
            if state.question_format == "mcq":
                if not hasattr(state, 'options') or not state.options or len(state.options) < 2:
                    raise ValueError(f"MCQ question at position {i} requires at least 2 options")
                if not hasattr(state, 'correct_answer') or not isinstance(state.correct_answer, int):
                    raise ValueError(f"MCQ question at position {i} requires integer correct_answer")
                if state.correct_answer < 0 or state.correct_answer >= len(state.options):
                    raise ValueError(f"MCQ question at position {i} correct_answer index out of bounds")
    
    # Validate END_NOTES has required fields
    end_notes_state = states[-1]
    if not hasattr(end_notes_state, 'summary') or not end_notes_state.summary:
        raise ValueError("END_NOTES page is missing summary")
    if not hasattr(end_notes_state, 'key_takeaways') or not end_notes_state.key_takeaways:
        raise ValueError("END_NOTES page is missing key_takeaways")
    
    # Validate no empty content blocks
    for i, state in enumerate(states):
        if state.type == "content":
            if not hasattr(state, 'text') or not state.text.strip():
                raise ValueError(f"Content page at position {i} has empty text")
    
    return True


def validate_lesson_structure(lesson: Lesson) -> bool:
    """
    Validate lesson structure against fixed templates.
    
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
    
    # Check first state is content
    if lesson.states[0].type != "content":
        raise ValueError("First state must be content")
    
    # Apply fixed template validation
    validate_duration_constraints(lesson.states, lesson.estimated_duration_minutes)
    
    return True
