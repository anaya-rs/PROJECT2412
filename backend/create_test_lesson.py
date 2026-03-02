#!/usr/bin/env python3
"""
Create a test lesson to verify frontend loading
"""

from core.db import get_db_session
from models.lesson import LessonDB
from domain.lesson import Lesson
from domain.state import ContentState, QuestionState, EndNotesState
from datetime import datetime

def create_test_lesson():
    """Create a test lesson in the database"""
    
    # Create test states
    states = [
        ContentState(
            type="content",
            id="content_1",
            text="This is a test lesson about basic programming concepts. Programming involves writing instructions that computers can execute."
        ),
        QuestionState(
            type="question",
            id="question_1",
            question_type="single_choice",
            prompt="What is the purpose of variables in programming?",
            options=["To store data", "To execute code", "To display output", "To compile programs"],
            correct_answers=[0],
            explanation="Variables are used to store data that can be manipulated during program execution."
        ),
        ContentState(
            type="content",
            id="content_2",
            text="Functions are reusable blocks of code that perform specific tasks. They help organize code and avoid repetition."
        ),
        QuestionState(
            type="question",
            id="question_2",
            question_type="single_choice",
            prompt="What is a function in programming?",
            options=["A storage location", "A reusable block of code", "A data type", "A programming language"],
            correct_answers=[1],
            explanation="Functions are reusable blocks of code that perform specific tasks."
        ),
        ContentState(
            type="content",
            id="content_3",
            text="Loops allow programs to repeat actions multiple times, making it easier to process large amounts of data."
        ),
        EndNotesState(
            type="end_notes",
            id="end_notes_4",
            summary="This lesson covered basic programming concepts including variables, functions, and loops.",
            key_takeaways=[
                "Variables store data in programs",
                "Functions are reusable code blocks",
                "Loops enable repetitive actions"
            ]
        )
    ]
    
    # Create lesson
    lesson = Lesson(
        schema_version="1.0",
        title="Test Programming Lesson",
        description="A beginner lesson about basic programming concepts",
        difficulty="beginner",
        estimated_duration_minutes=5,
        states=states
    )
    
    # Save to database
    db = get_db_session()
    try:
        lesson_db = LessonDB.from_domain(lesson, user_id=1)
        db.add(lesson_db)
        db.commit()
        
        print(f"✅ Test lesson created with ID: {lesson_db.id}")
        print(f"📝 Title: {lesson_db.title}")
        print(f"👤 User ID: {lesson_db.user_id}")
        print(f"📊 Duration: {lesson_db.estimated_duration_minutes} minutes")
        print(f"🔢 States: {len(states)}")
        
    finally:
        db.close()

if __name__ == "__main__":
    create_test_lesson()
