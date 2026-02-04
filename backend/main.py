"""
Main Application V2 - New Architecture Test
Simplified version to test new architecture without legacy complexity
"""

from fastapi import FastAPI, HTTPException, Header, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sqlite3
import os
import uuid
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional

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
    
    # Drop and recreate lessons table with correct schema
    cursor.execute("DROP TABLE IF EXISTS lessons")
    
    # Create lessons table with new schema
    cursor.execute("""
        CREATE TABLE lessons (
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

# ---------- Essential API Endpoints ----------

class AILessonJobRequest(BaseModel):
    text: str
    title: str = ""
    description: str = ""
    fileName: str = ""
    difficulty: str = "beginner"
    duration: int = 30
    questionCount: int = 3

class AIJobStatus(BaseModel):
    id: str
    userId: int
    status: str
    progress: int
    message: Optional[str] = None
    lessonId: Optional[int] = None

# In-memory job storage (simplified)
jobs: dict = {}

@app.post("/api/auth/login")
async def login(username: str = Form(...), password: str = Form(...)):
    """Simple login endpoint"""
    if username == "admin" and password == "password":
        return {"message": "Login successful", "token": "mock-token", "user": {"id": 1, "username": username}}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/lessons")
async def get_lessons():
    """Get lessons endpoint"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lessons ORDER BY created_at DESC")
    lessons = cursor.fetchall()
    conn.close()
    
    return {"lessons": [dict(lesson) for lesson in lessons]}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """File upload endpoint"""
    content = await file.read()
    text_content = content.decode('utf-8')
    return {"filename": file.filename, "text": text_content[:500] + "..." if len(text_content) > 500 else text_content}

@app.post("/api/ai/jobs")
async def start_ai_lesson_job(
    request: AILessonJobRequest,
    authorization: str = Header(None)
):
    """Start AI lesson generation with new architecture"""
    # Simple auth check
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Access token required")
    
    # Validate input
    if len(request.text) < 100:
        raise HTTPException(status_code=400, detail="Text content is too short (minimum 100 characters)")
    
    if request.duration not in [5, 30, 60]:
        raise HTTPException(status_code=400, detail="Duration must be 5, 30, or 60 minutes")
    
    # Create job
    job_id = str(uuid.uuid4())
    
    job = {
        "id": job_id,
        "userId": 1,
        "status": "queued",
        "progress": 0,
        "message": "Queued for generation",
        "text": request.text,
        "title": request.title,
        "description": request.description,
        "duration": request.duration,
        "difficulty": request.difficulty
    }
    
    jobs[job_id] = job
    
    # Process in background
    asyncio.create_task(process_ai_job_async(job_id, request))
    
    return {"jobId": job_id}

@app.get("/api/ai/jobs/{job_id}")
async def get_ai_lesson_job(job_id: str, authorization: str = Header(None)):
    """Get AI job status"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Access token required")
    
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]

async def process_ai_job_async(job_id: str, request: AILessonJobRequest):
    """Process AI job with new architecture"""
    try:
        # Update status
        jobs[job_id]["status"] = "running"
        jobs[job_id]["progress"] = 25
        jobs[job_id]["message"] = "Generating lesson content"
        
        # Generate lesson using new architecture
        generator = LessonGenerator(
            ollama_url=settings.OLLAMA_URL,
            model=settings.OLLAMA_MODEL
        )
        
        lesson = generator.generate_lesson(
            content=request.text,
            title=request.title,
            description=request.description,
            duration_minutes=request.duration,
            difficulty=request.difficulty
        )
        
        # Save lesson to database
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO lessons (title, description, start_node_id, nodes, transitions, metadata, schema_version, user_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lesson.title,
            request.description or f"Generated lesson about {lesson.title}",
            "start",
            '{"states": ' + lesson.json() + '}',
            '{}',
            f'{{"schema_version": "1.0", "engine_version": "fsm-v1", "estimated_duration_minutes": {lesson.estimated_duration_minutes}}}',
            "1.0",
            1,
            "2024-01-01T00:00:00Z",
            "2024-01-01T00:00:00Z"
        ))
        lesson_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Update status
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["message"] = "Lesson generated successfully"
        jobs[job_id]["lessonId"] = lesson_id
        
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["message"] = f"Generation failed: {str(e)}"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
