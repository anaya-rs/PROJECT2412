from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Header
from fastapi.middleware.cors import CORSMiddleware

from core import init_db, setup_logging
from core.dependencies import get_db, verify_authorization
from routers import lessons_router, sessions_router, analytics_router, auth_router, ai_router, upload_router, health

# explicit import of Depends to avoid any import issues
from fastapi import Depends as FastAPIDepends


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    setup_logging()
    init_db()
    yield
    # shutdown
    pass


def create_app() -> FastAPI:
    """create fastapi application"""
    
    app = FastAPI(
        title="AI Lesson Creator API",
        version="3.0.0",
        lifespan=lifespan
    )
    
    # Debug middleware to log CORS requests
    @app.middleware("http")
    async def debug_cors(request, call_next):
        origin = request.headers.get("origin")
        method = request.method
        path = request.url.path
        
        print(f"🔍 [CORS DEBUG] {method} {path} from origin: {origin}")
        
        response = await call_next(request)
        
        # Convert headers to dict safely (avoid datetime serialization issues)
        headers_dict = {}
        for key, value in response.headers.items():
            headers_dict[key] = str(value)
        
        print(f"🔍 [CORS DEBUG] Response headers: {headers_dict}")
        
        return response
    
    # add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8080", "http://localhost:8081", "http://localhost:80", "http://127.0.0.1:5173", "http://127.0.0.1:3000", "http://127.0.0.1:8080", "http://127.0.0.1:8081"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # include routers
    app.include_router(health.router)
    app.include_router(auth_router)
    app.include_router(ai_router)
    app.include_router(upload_router)
    app.include_router(lessons_router)
    app.include_router(sessions_router)
    app.include_router(analytics_router)
    
    # global exception handler with CORS headers
    @app.exception_handler(ValueError)
    async def value_error_handler(request, exc):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        from fastapi.responses import JSONResponse
        import traceback
        print(f"🔍 [ERROR] Unhandled exception: {exc}")
        print(f"🔍 [ERROR] Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
    
    # root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "AI Lesson Creator API", 
            "version": "3.0.0",
            "architecture": "clean"
        }
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "architecture": "production", "rag_enabled": True}
    
    @app.get("/test-auth")
    async def test_auth(user_id: int = Depends(verify_authorization)):
        return {"message": "Auth works", "user_id": user_id}
    
    return app


# create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5005)
