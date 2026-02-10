"""
Routers Module - HTTP endpoints only
"""

from .auth import router as auth_router
from .ai import router as ai_router
from .upload import router as upload_router
from .lessons import router as lessons_router
from .sessions import router as sessions_router
from .analytics import router as analytics_router

__all__ = [
    "auth_router",
    "ai_router",
    "upload_router",
    "lessons_router",
    "sessions_router", 
    "analytics_router"
]
