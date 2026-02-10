"""
Debug FSM behavior
"""

from domain.lesson import Lesson
from domain.state import ContentState, QuestionState
from domain.fsm import UserAction, step, LessonSession
from datetime import datetime
from uuid import uuid4

# Create test lesson
lesson = Lesson(
    schema_version="1.0",
    title="Test Lesson",
    estimated_duration_minutes=30,
    states=[
        ContentState(id="c1", type="content", text="First content"),
        QuestionState(
            id="q1",
            type="question",
            question_format="mcq",
            prompt="Test question 1",
            options=["A", "B"],
            correct_answer=0,
            explanation="Test explanation 1"
        ),
        ContentState(id="c2", type="content", text="Second content"),
        QuestionState(
            id="q2",
            type="question",
            question_format="mcq",
            prompt="Test question 2",
            options=["C", "D"],
            correct_answer=0,
            explanation="Test explanation 2"
        ),
        ContentState(id="c3", type="content", text="Third content"),
        QuestionState(
            id="q3",
            type="question",
            question_format="mcq",
            prompt="Test question 3",
            options=["E", "F"],
            correct_answer=0,
            explanation="Test explanation 3"
        ),
        ContentState(id="c4", type="content", text="Fourth content")
    ]
)

# Create session
session = LessonSession(
    id=str(uuid4()),
    lesson_id=1,
    user_id=1,
    current_index=6,  # Move to last content (index 6)
    attempts=0,
    started_at=datetime.utcnow(),
    last_active_at=datetime.utcnow()
)

# Test completion
action = UserAction(type="next")
result = step(lesson, session, action)

print("=== FSM Completion Debug ===")
print(f"Next index: {result.next_index}")
print(f"Next attempts: {result.next_attempts}")
print(f"Completed: {result.completed}")
print(f"Events count: {len(result.events)}")
for i, event in enumerate(result.events):
    print(f"Event {i}: {event.event_type} - {event.payload}")
print("========================")
