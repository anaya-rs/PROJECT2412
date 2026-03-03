"""
Migration script to add session_runtime table
"""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.config import settings


def create_session_runtime_table():
    """Create the session_runtime table"""
    
    # Extract database path from URL
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create session_runtime table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lesson_session_runtime (
                id TEXT PRIMARY KEY,
                lesson_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                current_index INTEGER DEFAULT 0 NOT NULL,
                attempts INTEGER DEFAULT 0 NOT NULL,
                session_data TEXT,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                last_active_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                completed_at DATETIME,
                FOREIGN KEY (lesson_id) REFERENCES lessons (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_runtime_lesson_id 
            ON lesson_session_runtime(lesson_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_runtime_user_id 
            ON lesson_session_runtime(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_runtime_started_at 
            ON lesson_session_runtime(started_at)
        """)
        
        conn.commit()
        print("✅ Session runtime table created successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating session runtime table: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    create_session_runtime_table()
