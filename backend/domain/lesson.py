"""
Domain Lesson Model - Pure logic, no database dependencies
"""

from typing import List, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

from .state import AuthoredState


class Lesson(BaseModel):
    """Immutable authored lesson artifact"""
    id: int | None = None  # DB primary key (optional for domain)
    schema_version: Literal["1.0"]
    title: str = Field(..., min_length=5, max_length=120)
    estimated_duration_minutes: Literal[5, 30, 60]
    states: List[AuthoredState]
    created_at: datetime | None = None

    @field_validator('states')
    @classmethod
    def validate_state_order(cls, states):
        if len(states) < 2:
            raise ValueError("Lesson must have multiple states")

        for i in range(len(states) - 1):
            if states[i].type == states[i + 1].type == "question":
                raise ValueError("Two questions cannot appear consecutively")

        return states

    @field_validator('states')
    @classmethod
    def validate_duration_structure(cls, states, info):
        values = info.data if hasattr(info, 'data') else {}
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
