"""
v 1.1 core dependencies - fastapi dependencies - database session management
"""

from fastapi import Depends, HTTPException, Header
from typing import Optional
from sqlalchemy.orm import Session
from contextlib import contextmanager
from .db import get_db_session
from utils.auth import verify_token
from .config import settings


@contextmanager
def get_db_context():
    """get database session context"""
    session = get_db_session()
    try:
        yield session
    finally:
        session.close()


def get_db() -> Session:
    """get database session dependency"""
    session = get_db_session()
    try:
        yield session
    finally:
        session.close()


def verify_authorization(authorization: Optional[str] = Header(None)):
    """verify jwt authorization header and return user_id"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="access token required")
    
    token = authorization.replace("Bearer ", "")
    try:
        print(f"🔍 [DEBUG] Using secret_key: {settings.JWT_SECRET}")
        payload = verify_token(token, settings.JWT_SECRET)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="invalid token")
        return int(user_id)
    except HTTPException:
        raise
    except Exception as e:
        print(f"🔍 [DEBUG] Auth error: {e}")
        raise HTTPException(status_code=401, detail="invalid token")
