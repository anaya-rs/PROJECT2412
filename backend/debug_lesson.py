import sqlite3

conn = sqlite3.connect('data/lessons.db')
cursor = conn.cursor()

cursor.execute('SELECT id, title, schema_version FROM lessons LIMIT 1')
lesson = cursor.fetchone()

if lesson:
    print(f'Lesson ID: {lesson[0]}')
    print(f'Title: {lesson[1]}')
    print(f'Schema Version: {lesson[2]}')
    print(f'Type: {type(lesson[2])}')

conn.close()
