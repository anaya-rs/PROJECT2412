"""
Lesson Models - Pydantic Schemas (Source of Truth)
These models define what a valid lesson is. If output doesn't pass this, it does not exist.
"""

from typing import List, Literal, Union
from pydantic import BaseModel, Field, validator


# ---------- Base ----------

class BaseState(BaseModel):
    id: str = Field(..., min_length=1)
    type: Literal["content", "question"]


# ---------- Content ----------

class ContentState(BaseState):
    type: Literal["content"]
    text: str = Field(..., min_length=20, max_length=900)


# ---------- Question ----------

class QuestionState(BaseState):
    type: Literal["question"]
    question_format: Literal["mcq", "short_answer"]
    prompt: str = Field(..., min_length=10, max_length=300)
    explanation: str = Field(..., min_length=20, max_length=500)

    # MCQ-only
    options: List[str] | None = None
    correct_answer: int | str

    @validator('options')
    def validate_mcq_options(cls, v, values):
        if values.get('question_format') == 'mcq':
            if not v or len(v) < 2:
                raise ValueError("MCQ requires at least 2 options")
        return v

    @validator('correct_answer')
    def validate_answer_type(cls, v, values):
        fmt = values.get('question_format')
        if fmt == 'mcq' and not isinstance(v, int):
            raise ValueError("MCQ correct_answer must be an index")
        if fmt == 'short_answer' and not isinstance(v, str):
            raise ValueError("short_answer requires string correct_answer")
        return v

    @validator('correct_answer')
    def validate_mcq_answer_bounds(cls, v, values):
        fmt = values.get('question_format')
        options = values.get('options')
        if fmt == 'mcq' and options is not None:
            if v < 0 or v >= len(options):
                raise ValueError("MCQ correct_answer index out of bounds")
        return v


AuthoredState = ContentState | QuestionState


# ---------- Lesson ----------

class Lesson(BaseModel):
    schema_version: Literal["1.0"]
    title: str = Field(..., min_length=5, max_length=120)
    estimated_duration_minutes: Literal[5, 30, 60]
    states: List[AuthoredState]

    @validator('states')
    def validate_state_order(cls, states):
        if len(states) < 2:
            raise ValueError("Lesson must have multiple states")

        for i in range(len(states) - 1):
            if states[i].type == states[i + 1].type == "question":
                raise ValueError("Two questions cannot appear consecutively")

        return states

    @validator('states')
    def validate_duration_structure(cls, states, values):
        duration = values.get('estimated_duration_minutes')
        
        # Duration templates
        duration_rules = {
            5: {"min_questions": 1, "max_questions": 2, "min_content": 1},
            30: {"min_questions": 3, "max_questions": 5, "min_content": 3},
            60: {"min_questions": 5, "max_questions": 8, "min_content": 5}
        }
        
        if duration in duration_rules:
            rules = duration_rules[duration]
            question_count = sum(1 for s in states if s.type == "question")
            content_count = sum(1 for s in states if s.type == "content")
            
            if question_count < rules["min_questions"]:
                raise ValueError(f"Duration {duration}min requires at least {rules['min_questions']} questions")
            if question_count > rules["max_questions"]:
                raise ValueError(f"Duration {duration}min allows at most {rules['max_questions']} questions")
            if content_count < rules["min_content"]:
                raise ValueError(f"Duration {duration}min requires at least {rules['min_content']} content blocks")
        
        return states


# ---------- Migration Types ----------

class LegacyLesson(BaseModel):
    """Legacy lesson format for migration purposes"""
    title: str
    description: str
    start_node_id: str
    nodes: dict
    transitions: dict
    metadata: dict = {}


class MigrationRequest(BaseModel):
    lesson_id: int
    target_duration: Literal[5, 30, 60] = 30


class MigrationResult(BaseModel):
    original_lesson_id: int
    new_lesson_id: int
    migrated_at: str
    schema_version: Literal["1.0"]
