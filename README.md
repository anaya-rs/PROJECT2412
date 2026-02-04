# Project2412 - AI-Powered Lesson Creator

A comprehensive lesson creation platform with AI integration, supporting both local LLM (Ollama) and cloud-based AI services.

## Features

### Core Functionality
- **AI-Powered Lesson Generation**: Create lessons from text using OpenAI or local LLM
- **Interactive Lesson Structure**: FSM-based lesson flow with content, questions, and feedback
- **File Upload Support**: TXT, PDF, DOCX file processing
- **Local LLM Integration**: Ollama support for privacy-focused AI processing
- **YouTube Integration**: Automatic video suggestions for lesson content
- **User Authentication**: JWT-based authentication system
- **Analytics Tracking**: Session and progress tracking

### Technical Stack
- **Backend**: Python FastAPI, SQLite
- **Frontend**: React, TypeScript, Tailwind CSS, shadcn/ui
- **AI Services**: OpenAI API, Ollama (Local LLM)
- **File Processing**: PyPDF2, python-docx
- **Authentication**: JWT tokens
- **Database**: SQLite with lessons and analytics tables

## Quick Start

### Prerequisites
- Python 3.8 or higher
- Node.js (v16 or higher) 
- Ollama (optional, for local LLM)
- OpenAI API Key (optional, for cloud AI)

### Installation

1. **Backend Setup (Python)**
   ```bash
   cd backend
   pip install -r requirements.txt
   python main.py
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Quick Start (Windows)**
   ```bash
   # Terminal 1 - Backend
   start-backend.bat
   
   # Terminal 2 - Frontend  
   start-frontend.bat
   ```

4. **Ollama Setup (Optional)**
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Download models
   ollama pull qwen2.5:1.5b
   ollama pull tinyllama
   ollama pull llama3.2
   ```

3. **Environment Configuration**
   ```env
   # Backend/.env
   PORT=5000
   JWT_SECRET=your-secret-key-here
   OPENAI_API_KEY=your-openai-key (optional)
   USE_LOCAL_LLM=true
   OLLAMA_URL=http://localhost:11434
   OLLAMA_MODEL=qwen2.5:1.5b
   YOUTUBE_API_KEY=your-youtube-key (optional)
   ```

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user info

### Lessons
- `GET /api/lessons` - Get all lessons
- `GET /api/lessons/:id` - Get specific lesson
- `POST /api/lessons` - Create new lesson
- `POST /api/lessons/ai-create` - Create AI-generated lesson
- `POST /api/init-sample` - Create sample lesson

### AI Services
- `POST /api/ai/generate-lesson` - Generate lesson from text
- `POST /api/ai/generate-questions` - Generate questions from text
- `POST /api/ai/generate-summary` - Generate summary
- `POST /api/ai/break-sections` - Break text into sections
- `GET /api/ai/test` - Test AI connections

### File Processing
- `POST /api/upload` - Upload and extract text from files

### Analytics
- `POST /api/analytics/session` - Create analytics session
- `PUT /api/analytics/session/:sessionId` - Update session

### System
- `GET /api/health` - Health check

## Database Schema

### Lessons Table
```sql
CREATE TABLE lessons (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  description TEXT,
  startNodeId TEXT NOT NULL,
  nodes TEXT NOT NULL, -- JSON
  transitions TEXT NOT NULL, -- JSON
  metadata TEXT, -- JSON
  createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
  updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Analytics Table
```sql
CREATE TABLE analytics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lessonId INTEGER,
  sessionId TEXT,
  startTime DATETIME,
  endTime DATETIME,
  visitedNodes TEXT, -- JSON
  userAnswers TEXT, -- JSON
  retryCount INTEGER DEFAULT 0,
  timePerNode TEXT, -- JSON
  dropOffPoints TEXT, -- JSON
  retryCounts TEXT, -- JSON
  paths TEXT, -- JSON
  createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
  updatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Lesson Structure

Lessons use a Finite State Machine (FSM) structure with the following node types:

- **START**: Welcome and introduction
- **CONTENT**: Educational text content
- **QUESTION**: Multiple choice questions
- **FEEDBACK**: Explanations and guidance
- **END**: Completion and summary

### Sample Lesson Flow
```
START → CONTENT1 → QUESTION1 → FEEDBACK1 → CONTENT2 → QUESTION2 → END
```

## AI Configuration

### Local LLM (Ollama)
- **Primary Model**: qwen2.5:1.5b (fast, educational)
- **Fallback**: tinyllama (testing)
- **Premium**: llama3.2 (best quality)

### Cloud AI (OpenAI)
- **Model**: gpt-3.5-turbo
- **Features**: Lesson generation, questions, summaries
- **Fallback**: Used when local LLM unavailable

## File Upload Support

- **TXT Files**: Direct text extraction
- **PDF Files**: Text extraction using pdf-parse
- **DOCX Files**: Text extraction using mammoth
- **Size Limit**: 10MB per file

## Security Features

- JWT-based authentication
- File upload validation
- SQL injection prevention
- XSS protection
- CORS configuration

## Development

### Running the Application
```bash
# Backend (Python)
cd backend
python main.py  # Production
# or
uvicorn main:app --reload  # Development with auto-reload

# Frontend
cd frontend
npm run dev  # Development
npm run build  # Production build
```

### Project Structure
```
Project2412/
├── backend/
│   ├── main.py            # FastAPI application (all functionality)
│   ├── requirements.txt   # Python dependencies
│   ├── .env              # Environment variables
│   ├── data/             # SQLite database (auto-created)
│   ├── uploads/          # File upload directory
│   └── start-backend.bat # Windows startup script
├── frontend/             # React TypeScript application
│   ├── src/
│   ├── package.json
│   └── start-frontend.bat
├── README.md
├── start-backend.bat
└── start-frontend.bat
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Change backend port
   PORT=5001 python main.py
   ```

2. **Database Errors**
   ```bash
   # Database is auto-created on first run
   # Delete data/lessons.db to reset
   ```

3. **Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ollama Connection Issues**
   ```bash
   ollama serve
   curl http://localhost:11434/api/tags
   ```

5. **File Upload Failures**
   - Check file size (max 10MB)
   - Verify file type support
   - Ensure uploads directory exists

### Environment Variables

Ensure all required environment variables are set in `backend/.env`:
- `PORT`: Server port (default: 5000)
- `JWT_SECRET`: JWT signing secret
- `OPENAI_API_KEY`: OpenAI API key (optional)
- `USE_LOCAL_LLM`: Enable local LLM (true/false)
- `OLLAMA_URL`: Ollama service URL
- `OLLAMA_MODEL`: Default Ollama model
- `YOUTUBE_API_KEY`: YouTube API key (optional)

## Performance Notes

### Local LLM Models
- **tinyllama**: Fastest, good for testing (~637MB)
- **qwen2.5:1.5b**: Balanced speed and quality (~986MB)
- **llama3.2**: Best quality, slower responses (~2GB)

### Optimization Tips
- Use local LLM for privacy and offline capability
- Enable YouTube integration for enhanced content
- Implement caching for repeated AI requests
- Use database indexes for better query performance

## License

MIT License - Feel free to modify and distribute.

---

**This is a production-ready lesson creation platform with AI integration capabilities.**
