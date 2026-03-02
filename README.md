# Project2412 - AI-Powered Lesson Creator

A production-ready lesson creation platform with AI integration, supporting both local LLM (Ollama) and cloud-based AI services.

## Features

- **AI-Powered Lesson Generation**: Create lessons from text using OpenAI or local LLM
- **Interactive Lesson Structure**: State-based lesson flow with content, questions, and feedback
- **File Upload Support**: TXT, PDF, DOCX file processing
- **Local LLM Integration**: Ollama support for privacy-focused AI processing
- **User Authentication**: JWT-based authentication system
- **Analytics Tracking**: Comprehensive session and progress tracking
- **Database Persistence**: SQLite with persistent session storage

## Tech Stack

- **Backend**: Python FastAPI, SQLAlchemy, SQLite
- **Frontend**: React, TypeScript, Tailwind CSS
- **AI Services**: OpenAI API, Ollama (Local LLM)
- **Authentication**: JWT tokens
- **Database**: SQLite with proper indexing

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Ollama (optional, for local LLM)

### Installation

1. **Backend Setup**
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

3. **Ollama Setup (Optional)**
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Download models
   ollama pull qwen2.5:1.5b
   ollama pull llama3.2
   ```

### Environment Configuration

Create `backend/.env`:
```env
PORT=5000
JWT_SECRET=your-secret-key-here
OPENAI_API_KEY=your-openai-key (optional)
USE_LOCAL_LLM=true
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:1.5b
```

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user

### Lessons
- `GET /api/lessons` - List all lessons
- `GET /api/lessons/:id` - Get specific lesson
- `POST /api/ai/jobs` - Create AI lesson generation job
- `GET /api/ai/jobs/:id` - Get job status

### Sessions
- `POST /api/sessions` - Start lesson session
- `GET /api/sessions/:id` - Get session state
- `POST /api/sessions/:id/answer` - Submit answer
- `POST /api/sessions/:id/next` - Advance to next state

### File Processing
- `POST /api/upload` - Upload and extract text from files

### System
- `GET /api/health` - Health check

## Database Schema

### Core Tables
- `lessons` - Lesson definitions and content
- `lesson_session_runtime` - Persistent session state
- `analytics_events` - User interaction tracking
- `users` - User authentication
- `jobs` - Background job tracking

## Architecture

### Services
- **LessonRuntimeService**: Session management with persistence
- **StatewiseLessonGenerator**: AI-powered lesson creation
- **JobService**: Background job processing
- **AnalyticsService**: Event tracking and insights
- **UserService**: Authentication and user management

### Lesson Structure
Lessons use a state-based approach:
- **Content**: Educational text
- **Question**: Multiple choice questions
- **End Notes**: Summary and key takeaways

## Development

### Project Structure
```
Project2412/
├── backend/
│   ├── services/         # Business logic
│   ├── models/          # Database models
│   ├── routers/         # API endpoints
│   ├── schemas/         # Pydantic models
│   ├── domain/          # Domain logic
│   ├── core/            # Core utilities
│   └── migrations/      # Database migrations
├── frontend/
│   ├── src/
│   │   ├── lib/        # API service
│   │   ├── components/  # React components
│   │   └── contexts/   # State management
└── docker-compose.yml   # Container orchestration
```

### Running Tests
```bash
# Backend
cd backend
python -m pytest

# Frontend
cd frontend
npm test
```

## Docker Deployment

```bash
# Development
docker-compose up

# Production
docker-compose -f docker-compose.prod.yml up
```

## Configuration

### Local LLM Models
- **qwen2.5:1.5b**: Fast, educational content
- **llama3.2**: High-quality responses
- **tinyllama**: Quick testing

### File Upload Support
- **TXT**: Direct text extraction
- **PDF**: Text extraction using PyPDF2
- **DOCX**: Text extraction using python-docx
- **Size Limit**: 10MB per file

## Security Features

- JWT-based authentication
- File upload validation
- SQL injection prevention
- XSS protection
- CORS configuration
- Structured error handling

## Performance

### Optimizations
- Database indexing for fast queries
- Persistent session storage
- Efficient AI prompt engineering
- Background job processing
- Comprehensive error handling

### Monitoring
- Structured logging
- Analytics tracking
- Health check endpoints
- Error response schemas

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   PORT=5001 python main.py
   ```

2. **Database Issues**
   ```bash
   # Reset database
   rm backend/data/*.db
   ```

3. **Ollama Connection**
   ```bash
   ollama serve
   curl http://localhost:11434/api/tags
   ```

## License

MIT License

---

**Production-ready with persistent sessions, analytics, and comprehensive error handling.**
