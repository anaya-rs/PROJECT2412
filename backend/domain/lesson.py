"""
domain lesson model - pure logic, no database dependencies
"""

from typing import List, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

from .state import AuthoredState, ContentState, QuestionState, EndNotesState


class Lesson(BaseModel):
    """immutable authored lesson artifact"""
    id: int | None = None  # db primary key (optional for domain)
    schema_version: Literal["1.0"]
    title: str = Field(..., min_length=5, max_length=120)
    description: str = Field(..., min_length=1, max_length=500)
    difficulty: Literal["beginner", "intermediate", "advanced"]
    estimated_duration_minutes: Literal[5, 15, 30]
    states: List[AuthoredState]
    created_at: datetime | None = None
    