from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
import sqlite3
import json
import os
import jwt
import hashlib
import aiofiles
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import requests
from PyPDF2 import PdfReader
from docx import Document
import uvicorn
from dotenv import load_dotenv
from jsonschema import Draft7Validator

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown
    pass

app = FastAPI(title="AI Lesson Creator API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8080", "http://localhost:8081", "http://localhost:8082"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

class Settings:
    def __init__(self):
        self.PORT = int(os.getenv("PORT", 5000))
        self.JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-here")
        self.OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
        self.MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10485760))
        
        print(f"Settings initialized:")
        print(f"  OLLAMA_URL: {self.OLLAMA_URL}")
        print(f"  OLLAMA_MODEL: {self.OLLAMA_MODEL}")

settings = Settings()

class User(BaseModel):
    id: int
    username: str
    email: str

class LoginRequest(BaseModel):
    username: str
    password: str

class LessonCreate(BaseModel):
    title: str
    description: Optional[str] = None
    startNodeId: str
    nodes: Dict[str, Any]
    transitions: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class AILessonRequest(BaseModel):
    text: str
    title: Optional[str] = None
    difficulty: Optional[str] = "beginner"
    duration: Optional[int] = 30
    questionCount: Optional[int] = 3

class AILessonJobRequest(BaseModel):
    text: str
    title: Optional[str] = None
    description: Optional[str] = None
    fileName: Optional[str] = None
    difficulty: Optional[str] = "beginner"
    duration: Optional[int] = 30
    questionCount: Optional[int] = 3

class AIJobStatus(BaseModel):
    id: str
    userId: int
    status: str
    progress: int
    message: Optional[str] = None
    lessonId: Optional[int] = None
    inputTitle: Optional[str] = None
    inputDescription: Optional[str] = None
    fileName: Optional[str] = None
    difficulty: Optional[str] = None
    duration: Optional[int] = None
    questionCount: Optional[int] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None

def create_ai_job(user_id: int, request: AILessonJobRequest) -> str:
    job_id = str(uuid.uuid4())
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO ai_jobs (id, userId, status, progress, message, inputTitle, inputDescription, fileName, difficulty, duration, questionCount)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job_id,
            user_id,
            "queued",
            0,
            "Queued",
            request.title,
            request.description,
            request.fileName,
            request.difficulty,
            request.duration,
            request.questionCount,
        ),
    )
    conn.commit()
    conn.close()
    return job_id

def update_ai_job(job_id: str, user_id: int, **fields):
    if not fields:
        return

    allowed = {
        "status",
        "progress",
        "message",
        "lessonId",
        "updatedAt",
    }
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return

    updates["updatedAt"] = datetime.now().isoformat()
    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values())

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE ai_jobs SET {set_clause} WHERE id = ? AND userId = ?",
        (*values, job_id, user_id),
    )
    conn.commit()
    conn.close()

def get_ai_job(job_id: str, user_id: int) -> Optional[dict]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ai_jobs WHERE id = ? AND userId = ?", (job_id, user_id))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def init_db():
    os.makedirs("data", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    
    conn = sqlite3.connect("data/lessons.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            startNodeId TEXT NOT NULL,
            nodes TEXT NOT NULL,
            transitions TEXT NOT NULL,
            metadata TEXT,
            createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
            updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lessonId INTEGER,
            sessionId TEXT,
            startTime DATETIME,
            endTime DATETIME,
            visitedNodes TEXT,
            userAnswers TEXT,
            retryCount INTEGER DEFAULT 0,
            timePerNode TEXT,
            dropOffPoints TEXT,
            retryCounts TEXT,
            paths TEXT,
            createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
            updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_jobs (
            id TEXT PRIMARY KEY,
            userId INTEGER NOT NULL,
            status TEXT NOT NULL,
            progress INTEGER NOT NULL DEFAULT 0,
            message TEXT,
            lessonId INTEGER,
            inputTitle TEXT,
            inputDescription TEXT,
            fileName TEXT,
            difficulty TEXT,
            duration INTEGER,
            questionCount INTEGER,
            createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
            updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect("data/lessons.db")
    conn.row_factory = sqlite3.Row
    return conn

def _load_authored_lesson_json_schema() -> dict:
    schema_path = os.path.join(os.path.dirname(__file__), "shared_schemas", "authoredLesson.schema.json")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

AUTHORED_LESSON_JSON_SCHEMA = _load_authored_lesson_json_schema()
AUTHORED_LESSON_VALIDATOR = Draft7Validator(AUTHORED_LESSON_JSON_SCHEMA)

def validate_authored_lesson_payload(payload: dict, duration_minutes: int) -> List[str]:
    errors: List[str] = []

    for e in sorted(AUTHORED_LESSON_VALIDATOR.iter_errors(payload), key=lambda x: str(x.path)):
        path = "/".join([str(p) for p in e.path])
        errors.append(f"{path}: {e.message}" if path else e.message)

    meta = (payload or {}).get("lesson_metadata") or {}
    if meta.get("estimated_duration_minutes") != duration_minutes:
        errors.append("lesson_metadata.estimated_duration_minutes must match requested duration")

    states = (payload or {}).get("states")
    if not isinstance(states, list):
        return errors

    ids = [s.get("id") for s in states if isinstance(s, dict)]
    if any((not isinstance(i, str) or not i) for i in ids):
        errors.append("All states must have a non-empty string id")
    if len(set(ids)) != len(ids):
        errors.append("State ids must be unique")

    ranges = {
        5: (4, 5),
        30: (14, 18),
        60: (26, 33),
    }
    if duration_minutes in ranges:
        min_states, max_states = ranges[duration_minutes]
        if len(states) < min_states or len(states) > max_states:
            errors.append(f"Invalid authored state count for {duration_minutes} minutes: {len(states)} (expected {min_states}..{max_states})")

    for idx, s in enumerate(states):
        if not isinstance(s, dict):
            continue
        if s.get("type") == "content":
            text = s.get("text")
            if isinstance(text, str):
                words = [w for w in text.strip().split() if w]
                if len(words) > 150:
                    errors.append(f"states[{idx}].text too long ({len(words)} words). Max 150.")

        if s.get("type") == "question":
            opts = s.get("options")
            correct = s.get("correct_answer")
            if isinstance(opts, list) and isinstance(correct, int):
                if correct < 0 or correct >= len(opts):
                    errors.append(f"states[{idx}].correct_answer out of range (0..{len(opts)-1})")

    question_count = sum(1 for s in states if isinstance(s, dict) and s.get("type") == "question")
    if question_count < 1:
        errors.append("Lesson must include at least 1 question")

    return errors

def authored_to_linear_nodes(authored: dict) -> Dict[str, Any]:
    states = authored.get("states") or []
    nodes: Dict[str, Any] = {}

    for i, s in enumerate(states):
        if not isinstance(s, dict):
            continue
        state_id = s.get("id")
        state_type = s.get("type")
        if not isinstance(state_id, str) or not state_id:
            continue

        next_id = states[i + 1].get("id") if i + 1 < len(states) and isinstance(states[i + 1], dict) else "end"
        if not isinstance(next_id, str) or not next_id:
            next_id = "end"

        if state_type == "content":
            nodes[state_id] = {
                "type": "content",
                "title": s.get("title") or "Content",
                "content": s.get("text") or "",
                "transitions": {"next": next_id},
            }
        elif state_type == "question":
            nodes[state_id] = {
                "type": "question",
                "title": s.get("title") or "Question",
                "content": "",
                "question": s.get("question") or "",
                "options": s.get("options") or [],
                "correctIndex": s.get("correct_answer"),
                "explanation": s.get("explanation") or "",
                "transitions": {"next": next_id},
            }

    if "end" not in nodes:
        nodes["end"] = {"type": "end", "title": "Done", "content": "Lesson complete!"}

    return nodes

def create_jwt_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")
    return encoded_jwt

def verify_jwt_token(token: str):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        return None

def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Access token required")
    
    try:
        token = authorization.split(" ")[1]
    except IndexError:
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    payload = verify_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    return payload

class AIService:
    def __init__(self):
        self.ollama_url = settings.OLLAMA_URL
        self.ollama_model = settings.OLLAMA_MODEL
    
    async def test_connection(self):
        try:
            response = await asyncio.to_thread(
                requests.get,
                f"{self.ollama_url}/api/tags",
                timeout=5,
            )
            ok = response.status_code == 200
        except Exception as e:
            print(f"Local LLM test failed: {e}")
            ok = False

        return {
            "success": ok,
            "services": {"localLLM": ok},
            "preferred": "local",
        }
    
    async def generate_lesson(self, text: str, options: Dict[str, Any] = None):
        if options is None:
            options = {}
        
        title = options.get("title", "Generated Lesson")
        difficulty = options.get("difficulty", "beginner")
        duration = options.get("duration", 30)
        question_count = options.get("questionCount", 3)
        
        try:
            result = await self._generate_with_local_llm(text, "lesson", options)
            if result:
                return {"success": True, "data": result, "model": "local"}
        except Exception as e:
            print(f"Local LLM failed: {e}")

        return {"success": False, "error": "Local LLM generation failed"}
    
    async def _generate_with_local_llm(self, text: str, task_type: str, options: Dict[str, Any]):
        try:
            title = (options or {}).get("title") or "Generated Lesson"
            difficulty = (options or {}).get("difficulty") or "beginner"
            duration = (options or {}).get("duration") or 30
            question_count = int((options or {}).get("questionCount") or 3)

            safe_text = (text or "")
            if len(safe_text) > 8000:
                safe_text = safe_text[:8000]

            prompt = (
                "You are generating an interactive lesson as authored states for a deterministic finite-state lesson engine.\n"
                "Return ONLY valid JSON. No markdown. No extra text.\n"
                "Do not include runtime states like feedback, retry, end. Only authored states.\n\n"
                "Output schema (must follow exactly):\n"
                "{\n"
                '  "lesson_metadata": {\n'
                '    "title": string,\n'
                '    "description": string (optional),\n'
                '    "estimated_duration_minutes": 5|30|60,\n'
                '    "difficulty": "beginner"|"intermediate"|"advanced" (optional)\n'
                "  },\n"
                '  "states": [\n'
                '    {"id": string, "type": "content", "title": string (optional), "text": string},\n'
                '    {"id": string, "type": "question", "question_format": "mcq", "question": string, "options": [string, ...], "correct_answer": number, "explanation": string}\n'
                "  ]\n"
                "}\n\n"
                "Rules:\n"
                f"- Difficulty: {difficulty}.\n"
                f"- estimated_duration_minutes MUST be exactly {duration}.\n"
                "- The lesson must be a linear sequence as given by the array order.\n"
                f"- Aim for ~{question_count} question states.\n"
                "- Content blocks must be short: max 150 words each.\n"
                "- Questions must include correct_answer (0-based index) and explanation.\n"
                "- Options must be 3 to 5 items.\n"
                "- No prose outside JSON fields.\n\n"
                f"Requested title: {title}\n\n"
                "Source material:\n"
                + safe_text
            )
            
            payload = {
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "max_tokens": 2000,
                },
            }

            response = await asyncio.to_thread(
                requests.post,
                f"{settings.OLLAMA_URL}/api/generate",
                json=payload,
                timeout=120,
            )
            
            print(f"Local LLM response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("response", "")
                print(f"Local LLM content length: {len(content)}")

                parsed = None
                try:
                    start = content.find("{")
                    end = content.rfind("}")
                    candidate = content[start : end + 1] if start != -1 and end != -1 and end > start else content
                    parsed = json.loads(candidate)
                except Exception:
                    parsed = None

                if isinstance(parsed, dict) and isinstance(parsed.get("lesson_metadata"), dict) and isinstance(parsed.get("states"), list):
                    return parsed

                return None
            else:
                print(f"Local LLM error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Local LLM exception: {e}")
            return None

ai_service = AIService()

@app.get("/api/health")
async def health_check():
    return {"status": "OK", "timestamp": datetime.now().isoformat()}

@app.post("/api/auth/login")
async def login(login_data: LoginRequest):
    users = [
        {"id": 1, "username": "admin", "email": "admin@example.com", "password": "password"},
        {"id": 2, "username": "teacher", "email": "teacher@example.com", "password": "password"}
    ]
    
    user = next((u for u in users if u["username"] == login_data.username or u["email"] == login_data.username), None)
    
    if not user or user["password"] != login_data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_jwt_token({
        "userId": user["id"],
        "username": user["username"],
        "email": user["email"]
    })
    
    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"]
        }
    }

@app.get("/api/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return {"user": current_user}

@app.get("/api/lessons")
async def get_lessons():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lessons ORDER BY createdAt DESC")
    lessons = cursor.fetchall()
    conn.close()
    
    result = []
    for lesson in lessons:
        lesson_dict = dict(lesson)
        lesson_dict["nodes"] = json.loads(lesson_dict["nodes"])
        lesson_dict["transitions"] = json.loads(lesson_dict["transitions"])
        if lesson_dict["metadata"]:
            lesson_dict["metadata"] = json.loads(lesson_dict["metadata"])
        result.append(lesson_dict)
    
    return result

@app.get("/api/lessons/{lesson_id}")
async def get_lesson(lesson_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,))
    lesson = cursor.fetchone()
    conn.close()
    
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    lesson_dict = dict(lesson)
    lesson_dict["nodes"] = json.loads(lesson_dict["nodes"])
    lesson_dict["transitions"] = json.loads(lesson_dict["transitions"])
    if lesson_dict["metadata"]:
        lesson_dict["metadata"] = json.loads(lesson_dict["metadata"])
    
    return lesson_dict

@app.post("/api/lessons")
async def create_lesson(lesson: LessonCreate, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO lessons (title, description, startNodeId, nodes, transitions, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        lesson.title,
        lesson.description,
        lesson.startNodeId,
        json.dumps(lesson.nodes),
        json.dumps(lesson.transitions),
        json.dumps(lesson.metadata) if lesson.metadata else None
    ))
    
    lesson_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": lesson_id, **lesson.model_dump()}

@app.delete("/api/lessons/{lesson_id}")
async def delete_lesson(lesson_id: int, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM lessons WHERE id = ?", (lesson_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="Lesson not found")

    return {"success": True}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")
    
    file_path = f"uploads/{file.filename}"
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    extracted_text = ""
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    try:
        if file_extension == '.txt':
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                extracted_text = await f.read()
        
        elif file_extension == '.pdf':
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                extracted_text = ""
                for page in reader.pages:
                    extracted_text += page.extract_text()
        
        elif file_extension == '.docx':
            doc = Document(file_path)
            extracted_text = "\\n".join([paragraph.text for paragraph in doc.paragraphs])
        
        else:
            extracted_text = "Unsupported file type. Please use TXT, PDF, or DOCX files."
    
    except Exception as e:
        extracted_text = f"File processing failed: {str(e)}"
    
    finally:
        os.remove(file_path)
    
    return {
        "fileName": file.filename,
        "fileType": file.content_type,
        "fileSize": len(content),
        "text": extracted_text,
        "wordCount": len(extracted_text.split()),
        "characterCount": len(extracted_text)
    }

@app.post("/api/ai/generate-lesson")
async def generate_ai_lesson(request: AILessonRequest, current_user: dict = Depends(get_current_user)):
    if len(request.text) < 100:
        raise HTTPException(status_code=400, detail="Text content is too short (minimum 100 characters)")

    duration = int(request.duration or 30)
    attempts = 0
    last_errors: List[str] = []

    while attempts < 3:
        attempts += 1
        result = await ai_service.generate_lesson(
            request.text,
            {
                "title": request.title,
                "difficulty": request.difficulty,
                "duration": duration,
                "questionCount": request.questionCount,
            },
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error") or "AI generation failed")

        authored = result.get("data") or {}
        errors = validate_authored_lesson_payload(authored, duration)
        if not errors:
            return {"success": True, "lesson": authored}

        last_errors = errors

    raise HTTPException(status_code=422, detail={"message": "Generated lesson failed validation", "errors": last_errors})

async def _process_ai_job(job_id: str, user_id: int, request: AILessonJobRequest):
    try:
        update_ai_job(job_id, user_id, status="running", progress=10, message="Generating lesson")

        duration = int(request.duration or 30)
        attempts = 0
        authored: Dict[str, Any] = {}
        last_errors: List[str] = []

        while attempts < 3:
            attempts += 1
            result = await ai_service.generate_lesson(
                request.text,
                {
                    "title": request.title,
                    "difficulty": request.difficulty,
                    "duration": duration,
                    "questionCount": request.questionCount,
                },
            )

            if not result.get("success"):
                update_ai_job(job_id, user_id, status="failed", progress=100, message=result.get("error") or "AI generation failed")
                return

            authored = result.get("data") or {}
            errors = validate_authored_lesson_payload(authored, duration)
            if not errors:
                break

            last_errors = errors
            authored = {}

        if not authored:
            update_ai_job(job_id, user_id, status="failed", progress=100, message=f"Generated lesson failed validation: {last_errors[:3]}")
            return

        update_ai_job(job_id, user_id, progress=70, message="Saving lesson")
        lesson_data = authored

        meta = lesson_data.get("lesson_metadata") or {}
        final_title = request.title or meta.get("title") or "Untitled Lesson"
        final_description = request.description or meta.get("description") or ""

        nodes = authored_to_linear_nodes(lesson_data)
        authored_states = lesson_data.get("states") or []
        start_node_id = authored_states[0].get("id") if authored_states and isinstance(authored_states[0], dict) else "start"

        metadata = {
            "difficulty": request.difficulty,
            "duration": request.duration,
            "questionCount": request.questionCount,
            "fileName": request.fileName,
            "generatedBy": result.get("model") or "ai",
            "aiGenerated": True,
        }

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO lessons (title, description, startNodeId, nodes, transitions, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                final_title,
                final_description,
                start_node_id,
                json.dumps(nodes),
                json.dumps({}),
                json.dumps(metadata),
            ),
        )
        lesson_id = cursor.lastrowid
        conn.commit()
        conn.close()

        update_ai_job(job_id, user_id, status="completed", progress=100, message="Lesson created", lessonId=lesson_id)
    except Exception as e:
        update_ai_job(job_id, user_id, status="failed", progress=100, message=str(e))

@app.post("/api/ai/jobs")
async def start_ai_lesson_job(request: AILessonJobRequest, current_user: dict = Depends(get_current_user)):
    if len(request.text) < 100:
        raise HTTPException(status_code=400, detail="Text content is too short (minimum 100 characters)")

    user_id = int(current_user.get("userId"))
    job_id = create_ai_job(user_id, request)
    asyncio.create_task(_process_ai_job(job_id, user_id, request))
    return {"jobId": job_id}

@app.get("/api/ai/jobs/{job_id}")
async def get_ai_lesson_job(job_id: str, current_user: dict = Depends(get_current_user)):
    user_id = int(current_user.get("userId"))
    job = get_ai_job(job_id, user_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/api/ai/test")
async def test_ai_connection(current_user: dict = Depends(get_current_user)):
    return await ai_service.test_connection()

@app.post("/api/analytics/session")
async def create_analytics_session(
    lessonId: int = Form(...),
    sessionId: str = Form(...),
    startTime: Optional[str] = Form(None)
):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO analytics (lessonId, sessionId, startTime, visitedNodes, userAnswers, retryCount, timePerNode, dropOffPoints, retryCounts, paths)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        lessonId,
        sessionId,
        startTime or datetime.now().isoformat(),
        json.dumps([]),
        json.dumps({}),
        json.dumps({}),
        json.dumps({}),
        json.dumps([]),
        json.dumps({}),
        json.dumps([])
    ))
    
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": session_id, "lessonId": lessonId, "sessionId": sessionId}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
