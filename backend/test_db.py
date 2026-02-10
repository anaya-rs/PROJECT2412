"""
Simple database test
"""

from core.db import get_db
from models.lesson import LessonDB

def test_db():
    """Test database connection"""
    with get_db() as db:
        lessons = db.query(LessonDB).all()
        print(f"Found {len(lessons)} lessons")
        for lesson in lessons:
            print(f"Lesson: {lesson.title}")

if __name__ == "__main__":
    test_db()
