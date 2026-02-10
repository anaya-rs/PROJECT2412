"""
Domain State Models - Pure logic, no database dependencies
"""

from typing import List, Literal, Union
from pydantic import BaseModel, Field, field_validator


class BaseState(BaseModel):
    type: Literal["content", "question", "end_notes"]
    id: str = Field(..., min_length=1)


class ContentState(BaseState):
    type: Literal["content"]
    text: str = Field(..., min_length=1, max_length=900)


class QuestionState(BaseState):
    type: Literal["question"]
    question_format: Literal["mcq", "short_answer"]
    prompt: str = Field(..., min_length=10, max_length=300)
    explanation: str = Field(..., min_length=1, max_length=500)

    # MCQ-only
    options: List[str] | None = None
    correct_answer: int | str

    @field_validator('options')
    @classmethod
    def validate_mcq_options(cls, v, info):
        values = info.data if hasattr(info, 'data') else {}
        if values.get('question_format') == 'mcq':
            if not v or len(v) < 2:
                raise ValueError("MCQ requires at least 2 options")
        return v

    @field_validator('correct_answer')
    @classmethod
    def validate_answer_type(cls, v, info):
        values = info.data if hasattr(info, 'data') else {}
        fmt = values.get('question_format')
        if fmt == 'mcq' and not isinstance(v, int):
            raise ValueError("MCQ correct_answer must be an index")
        if fmt == 'short_answer' and not isinstance(v, str):
            raise ValueError("short_answer requires string correct_answer")
        return v

    @field_validator('correct_answer')
    @classmethod
    def validate_mcq_answer_bounds(cls, v, info):
        values = info.data if hasattr(info, 'data') else {}
        fmt = values.get('question_format')
        options = values.get('options')
        if fmt == 'mcq' and options is not None:
            if v < 0 or v >= len(options):
                raise ValueError("MCQ correct_answer index out of bounds")
        return v


class EndNotesState(BaseState):
    type: Literal["end_notes"]
    summary: str = Field(..., min_length=1, max_length=900)
    key_takeaways: List[str] = Field(..., min_items=1, max_items=5)


# Use discriminator for proper union validation
AuthoredState = Union[ContentState, QuestionState, EndNotesState]


# Domain Events (pure, no persistence)
class DomainEvent(BaseModel):
    event_type: Literal["enter", "answer", "retry", "advance", "complete"]
    payload: dict
