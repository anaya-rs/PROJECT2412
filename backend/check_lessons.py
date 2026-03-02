#!/usr/bin/env python3
"""
Check lessons in database
"""

import sys
sys.path.append('.')
from core.db import init_db, get_db_session
from models.lesson import LessonDB
import json

def main():
    # Initialize database
    init_db()

    # Check existing lessons
    session = get_db_session()
    lessons = session.query(LessonDB).all()
    print(f'Total lessons in database: {len(lessons)}')

    for lesson in lessons[:3]:  # Show first 3
        print(f'Lesson ID: {lesson.id}')
        print(f'Title: {lesson.title}')
        print(f'States JSON length: {len(lesson.states) if lesson.states else 0}')
        if lesson.states:
            try:
                states_data = json.loads(lesson.states)
                print(f'Number of states: {len(states_data)}')
                if states_data:
                    print(f'First state type: {states_data[0].get("type", "unknown")}')
                    print(f'First state content preview: {str(states_data[0])[:200]}...')
            except Exception as e:
                print(f'Error parsing states JSON: {e}')
        print('---')

    session.close()

if __name__ == "__main__":
    main()
