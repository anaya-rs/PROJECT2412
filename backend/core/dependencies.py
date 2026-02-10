"""
FastAPI Dependencies - Database session management
"""

from fastapi import Depends, HTTPException, Header
from typing import Optional
from .db import get_db_session


def get_current_db():
    """Get database session for FastAPI dependency injection"""
    return get_db_session()


def verify_authorization(authorization: Optional[str] = Header(None)):
    """Verify authorization header and return user_id"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Access token required")
    
    # Mock user ID extraction - in production use proper JWT
    return 1
