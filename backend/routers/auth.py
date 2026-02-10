"""
Authentication Router - Login and user management
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login(credentials: Dict[str, str]) -> Dict[str, Any]:
    """
    Mock login endpoint - accepts any username/password and returns a token
    In production, this would validate against actual user credentials
    """
    username = credentials.get("username", "")
    password = credentials.get("password", "")
    
    # Mock validation - in production, check against database
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")
    
    # Mock successful login - return a fake token
    return {
        "token": "mock-token-12345",
        "user": {
            "id": 1,
            "username": username,
            "email": f"{username}@example.com"
        }
    }


@router.post("/logout")
async def logout() -> Dict[str, str]:
    """Mock logout endpoint"""
    return {"message": "Logged out successfully"}
