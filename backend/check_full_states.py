import sqlite3
import json

conn = sqlite3.connect('data/lessons.db')
cursor = conn.cursor()

# Get full states data for first lesson
cursor.execute('SELECT id, title, states FROM lessons LIMIT 1')
lesson = cursor.fetchone()

if lesson:
    print(f'Lesson ID: {lesson[0]}')
    print(f'Title: {lesson[1]}')
    print(f'States length: {len(lesson[2])}')
    
    try:
        states_data = json.loads(lesson[2])
        print(f'Number of states: {len(states_data)}')
        
        for i, state in enumerate(states_data):
            print(f'\n--- State {i+1} ---')
            print(f'Type: {state.get("type")}')
            print(f'ID: {state.get("id")}')
            
            if state.get("type") == "content":
                print(f'Text: {state.get("text", "EMPTY")[:100]}...')
            elif state.get("type") == "question":
                print(f'Question Type: {state.get("question_type")}')
                print(f'Prompt: {state.get("prompt", "EMPTY")[:100]}...')
                print(f'Options: {state.get("options", [])}')
                print(f'Correct Answers: {state.get("correct_answers", [])}')
            elif state.get("type") == "end_notes":
                print(f'Summary: {state.get("summary", "EMPTY")[:100]}...')
                print(f'Key Takeaways: {state.get("key_takeaways", [])}')
            
    except json.JSONDecodeError as e:
        print(f'JSON decode error: {e}')
        print(f'Raw states: {lesson[2][:500]}')

conn.close()
