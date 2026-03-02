"""
domain state models
"""

from typing import List, Literal, Union
from pydantic import BaseModel, Field, field_validator, model_validator


class BaseState(BaseModel):
    type: Literal["content", "question", "end_notes"]
    id: str = Field(..., min_length=1)


class ContentState(BaseState):
    type: Literal["content"]
    text: str = Field(..., min_length=1, max_length=900)


class QuestionState(BaseState):
    type: Literal["question"] = "question"
    question_type: Literal["single_choice", "multiple_choice"]
    prompt: str = Field(min_length=5)
    options: List[str] = Field(min_length=2, max_length=8)
    correct_answers: List[int] = Field(min_length=1)
    explanation: str = Field(min_length=5)

    @model_validator(mode="after")
    def validate_question(self):
        # validate correct answer bounds
        for idx in self.correct_answers:
            if idx < 0 or idx >= len(self.options):
                raise ValueError("correct answer index out of bounds")

        # enforce single choice constraint
        if self.question_type == "single_choice" and len(self.correct_answers) != 1:
            raise ValueError("single choice must have exactly one correct answer")

        # enforce multiple choice constraint
        if self.question_type == "multiple_choice" and len(self.correct_answers) < 1:
            raise ValueError("multiple choice must have at least one correct answer")

        return self


class EndNotesState(BaseState):
    type: Literal["end_notes"]
    summary: str = Field(..., min_length=1, max_length=900)
    key_takeaways: List[str] = Field(..., min_items=1, max_items=5)


# use discriminator for proper union validation
AuthoredState = Union[ContentState, QuestionState, EndNotesState]


# domain events (pure, no persistence)
class DomainEvent(BaseModel):
    event_type: Literal["enter", "answer", "retry", "advance", "complete"]
    payload: dict
