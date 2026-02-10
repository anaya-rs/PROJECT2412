"""
Debug completion logic step by step
"""

from domain.lesson import Lesson
from domain.state import ContentState, QuestionState
from domain.fsm import UserAction, step, LessonSession
from datetime import datetime
from uuid import uuid4

# Simple lesson with 3 states
lesson = Lesson(
    schema_version="1.0",
    title="Test Lesson",
    estimated_duration_minutes=5,  # Use 5 min for simplicity
    states=[
        ContentState(id="c1", type="content", text="First content"),
        QuestionState(id="q1", type="question", question_format="mcq",
                   prompt="Test question", options=["A", "B"], correct_answer=0, explanation="Test explanation"),
        ContentState(id="c2", type="content", text="Last content")
    ]
)

session = LessonSession(
    id=str(uuid4()),
    lesson_id=1,
    user_id=1,
    current_index=1,  # Start at question
    attempts=0,
    started_at=datetime.utcnow(),
    last_active_at=datetime.utcnow()
)

print("=== Step 1: Wrong Answer (first attempt) ===")
action = UserAction(type="answer", payload={"answer": 1})  # Wrong answer
result = step(lesson, session, action)
print(f"Next index: {result.next_index}")
print(f"Completed: {result.completed}")
print(f"Events: {len(result.events)}")
print()

print("=== Step 2: Wrong Answer (second attempt) ===")
session.current_index = result.next_index
session.attempts = result.next_attempts
action = UserAction(type="answer", payload={"answer": 2})  # Another wrong answer
result = step(lesson, session, action)
print(f"Next index: {result.next_index}")
print(f"Completed: {result.completed}")
print(f"Events: {len(result.events)}")
print()

print("=== Step 3: Next from last content ===")
session.current_index = result.next_index
session.attempts = result.next_attempts
action = UserAction(type="next")
result = step(lesson, session, action)
print(f"Next index: {result.next_index}")
print(f"Completed: {result.completed}")
print(f"Events: {len(result.events)}")
print()

print("=== Step 4: Check final state ===")
print(f"Final next_index: {result.next_index}")
print(f"Final completed: {result.completed}")
print(f"Lesson has {len(lesson.states)} states")
print(f"Next index >= len(states): {result.next_index >= len(lesson.states)}")
