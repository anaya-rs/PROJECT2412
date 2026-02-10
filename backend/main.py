"""
Main Application - Clean architecture, app creation only
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Header
from fastapi.middleware.cors import CORSMiddleware

from core import init_db, setup_logging, get_settings
from core.dependencies import get_current_db, verify_authorization
from routers import lessons_router, sessions_router, analytics_router, auth_router, ai_router, upload_router

# Explicit import of Depends to avoid any import issues
from fastapi import Depends as FastAPIDepends


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    init_db()
    yield
    # Shutdown
    pass


def create_app() -> FastAPI:
    """Create FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title="AI Lesson Creator API",
        version="3.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(auth_router)
    app.include_router(ai_router)
    app.include_router(upload_router)
    app.include_router(lessons_router)
    app.include_router(sessions_router)
    app.include_router(analytics_router)
    
    # Global exception handler
    @app.exception_handler(ValueError)
    async def value_error_handler(request, exc):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)}
        )
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "AI Lesson Creator API", 
            "version": "3.0.0",
            "architecture": "clean"
        }
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "architecture": "clean"}
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5002)
