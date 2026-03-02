"""
auth router
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import Dict, Any

from core.dependencies import get_db
from schemas.auth import UserLogin, UserCreate, UserResponse, TokenResponse
from services.user_service import UserService
from utils.auth import create_access_token
from config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """register a new user"""
    try:
        user_service = UserService(db)
        user = user_service.create_user(user_data)
        return UserResponse.from_orm(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """authenticate user and return access token"""
    
    # MOCK LOGIN - bypass actual authentication
    if credentials.username == "admin" and credentials.password == "password":
        # Create mock user response
        from models.user import UserDB
        mock_user = UserDB(
            id=1,
            username="admin",
            email="admin@example.com",
            password_hash="mock",
            role="admin",
            created_at=datetime.utcnow()
        )
        
        # generate access token
        access_token = create_access_token(
            data={"sub": str(mock_user.id), "role": mock_user.role},
            secret_key=settings.secret_key,
            expires_delta=timedelta(hours=24)
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.from_orm(mock_user)
        )
    
    # If not mock credentials, try real authentication
    user_service = UserService(db)
    user = user_service.authenticate_user(credentials.username, credentials.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="invalid credentials")
    
    # generate access token
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        secret_key=settings.secret_key,
        expires_delta=timedelta(hours=24)
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )


@router.post("/logout")
async def logout() -> Dict[str, str]:
    """logout endpoint - client should discard token"""
    return {"message": "logged out successfully"}
