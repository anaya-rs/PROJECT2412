"""
Main Application V2 - New Architecture Test
Simplified version to test new architecture without legacy complexity
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sqlite3
import os
from dotenv import load_dotenv

# Import new architecture modules
from lessons import Lesson, LessonGenerator, LessonGenerationError
from analytics import AnalyticsCollector

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    run_migrations()
    yield
    # Shutdown
    pass

app = FastAPI(title="AI Lesson Creator API V2", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8080", "http://localhost:8081", "http://localhost:8082"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Settings:
    def __init__(self):
        self.OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
        
        print(f"Settings initialized:")
        print(f"  OLLAMA_URL: {self.OLLAMA_URL}")
        print(f"  OLLAMA_MODEL: {self.OLLAMA_MODEL}")

settings = Settings()

def init_db():
    """Initialize database with new schema"""
    os.makedirs("data", exist_ok=True)
    
    conn = sqlite3.connect("data/lessons.db")
    cursor = conn.cursor()
    
    # Create lessons table with new schema
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            start_node_id TEXT NOT NULL,
            nodes TEXT NOT NULL,
            transitions TEXT NOT NULL,
            metadata TEXT,
            schema_version TEXT DEFAULT 'legacy',
            user_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def run_migrations():
    """Run database migrations"""
    conn = sqlite3.connect("data/lessons.db")
    cursor = conn.cursor()
    
    # Create lesson events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lesson_events (
            id TEXT PRIMARY KEY,
            lesson_id INTEGER,
            user_id INTEGER,
            state_id TEXT,
            event_type TEXT,
            payload TEXT,
            created_at TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("Database migrations completed")

def get_db():
    conn = sqlite3.connect("data/lessons.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------- API Endpoints ----------

@app.get("/")
async def root():
    return {"message": "AI Lesson Creator API V2", "version": "2.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "architecture": "v2"}

@app.post("/api/v2/lessons/test")
async def test_new_architecture():
    """Test endpoint to verify new architecture works"""
    try:
        # Test lesson creation
        lesson_data = {
            "schema_version": "1.0",
            "title": "Test Lesson",
            "estimated_duration_minutes": 5,
            "states": [
                {
                    "id": "c_1",
                    "type": "content",
                    "text": "This is test content for the lesson."
                },
                {
                    "id": "q_1",
                    "type": "question",
                    "question_format": "mcq",
                    "prompt": "What is this?",
                    "options": ["Test", "Lesson", "API", "V2"],
                    "correct_answer": 2,
                    "explanation": "This is a test lesson."
                }
            ]
        }
        
        lesson = Lesson.model_validate(lesson_data)
        
        # Test FSM
        from lessons.fsm import LessonFSM
        fsm = LessonFSM(lesson.states)
        
        # Test analytics
        conn = get_db()
        analytics = AnalyticsCollector(conn)
        event_id = analytics.track_event(
            lesson_id=1,
            user_id=1,
            event_type="test",
            state_id="test"
        )
        conn.close()
        
        return {
            "success": True,
            "lesson_validated": True,
            "fsm_created": True,
            "analytics_tracking": True,
            "event_id": event_id,
            "states_count": len(lesson.states),
            "fsm_progress": fsm.progress
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
