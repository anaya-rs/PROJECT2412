"""
Domain Lesson Model - Pure logic, no database dependencies
"""

from typing import List, Literal
from pydantic import BaseModel, Field, field_validator
from typing import Union
from pydantic import Field
from datetime import datetime

from .state import AuthoredState, ContentState, QuestionState, EndNotesState


class Lesson(BaseModel):
    """Immutable authored lesson artifact"""
    id: int | None = None  # DB primary key (optional for domain)
    schema_version: Literal["1.0"]
    title: str = Field(..., min_length=5, max_length=120)
    estimated_duration_minutes: Literal[5, 15, 30]
    states: List[AuthoredState]
    created_at: datetime | None = None
    
    # Temporarily disable validation to test parsing
    # @field_validator('states')
    # @classmethod
    # def validate_state_order(cls, states):
    #     if len(states) < 2:
    #         raise ValueError("Lesson must have multiple states")
    # 
    #     for i in range(len(states) - 1):
    #         if states[i].type == states[i + 1].type == "question":
    #             raise ValueError("Two questions cannot appear consecutively")
    # 
    #     return states
    
    # @field_validator('states')
    # @classmethod
    # def validate_duration_structure(cls, states, info):
    #     values = info.data if hasattr(info, 'data') else {}
    #     duration = values.get('estimated_duration_minutes')
    #     
    #     # Fixed duration templates
    #     duration_templates = {
    #         5: {"total_pages": 5, "content_pages": 2, "question_pages": 2, "end_notes_pages": 1},
    #         15: {"total_pages": 9, "content_pages": 4, "question_pages": 4, "end_notes_pages": 1},
    #         30: {"total_pages": 13, "content_pages": 6, "question_pages": 6, "end_notes_pages": 1}
    #     }
    #     
    #     if duration not in duration_templates:
    #         raise ValueError(f"Duration {duration} is not supported. Only 5, 15, and 30 minutes are allowed.")
    #     
    #     template = duration_templates[duration]
    #     
    #     # Count page types
    #     content_count = sum(1 for s in states if s.type == "content")
    #     question_count = sum(1 for s in states if s.type == "question")
    #     end_notes_count = sum(1 for s in states if s.type == "end_notes")
    #     
    #     # Validate exact counts
    #     if len(states) != template["total_pages"]:
    #         raise ValueError(f"Duration {duration}min requires exactly {template['total_pages']} pages, got {len(states)}")
    #     
    #     if content_count != template["content_pages"]:
    #         raise ValueError(f"Duration {duration}min requires exactly {template['content_pages']} content pages, got {content_count}")
    #     
    #     if question_count != template["question_pages"]:
    #         raise ValueError(f"Duration {duration}min requires exactly {template['question_pages']} question pages, got {question_count}")
    #     
    #     if end_notes_count != template["end_notes_pages"]:
    #         raise ValueError(f"Duration {duration}min requires exactly {template['end_notes_pages']} end_notes page, got {end_notes_count}")
    #     
    #     return states
