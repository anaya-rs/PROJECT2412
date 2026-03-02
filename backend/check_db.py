import sqlite3

conn = sqlite3.connect('data/lessons.db')
cursor = conn.cursor()

# Check tables
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
print('Tables:', tables)

if tables:
    # Check lessons table structure
    cursor.execute('PRAGMA table_info(lessons)')
    columns = cursor.fetchall()
    print('\nLesson table columns:')
    for col in columns:
        print(f'  {col[1]} ({col[2]})')
    
    # Check sample data
    cursor.execute('SELECT id, title, length(states) FROM lessons LIMIT 3')
    rows = cursor.fetchall()
    print('\nSample records:')
    for row in rows:
        print(f'ID: {row[0]}, Title: {row[1]}, States length: {row[2]}')
    
    # Check actual states content
    cursor.execute('SELECT id, title, states FROM lessons LIMIT 1')
    lesson = cursor.fetchone()
    if lesson:
        print(f'\nFirst lesson (ID: {lesson[0]}):')
        print(f'Title: {lesson[1]}')
        print(f'States JSON: {lesson[2][:200]}...')

conn.close()
