"""
user service
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash
from models.user import UserDB
from schemas.auth import UserCreate

logger = logging.getLogger(__name__)


class UserService:
    
    def __init__(self, db):
        self.db = db
    
    def create_user(self, user_data: UserCreate) -> UserDB:
        # check if user already exists
        existing_user = self.db.query(UserDB).filter(
            (UserDB.username == user_data.username) | (UserDB.email == user_data.email)
        ).first()
        
        if existing_user:
            raise ValueError("user with this username or email already exists")
        
        # hash password
        password_hash = generate_password_hash(user_data.password)
        
        # create user
        user = UserDB(
            username=user_data.username,
            email=user_data.email,
            password_hash=password_hash
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def get_user_by_username(self, username: str) -> Optional[UserDB]:
        return self.db.query(UserDB).filter(UserDB.username == username).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[UserDB]:
        return self.db.query(UserDB).filter(UserDB.id == user_id).first()
    
    def authenticate_user(self, username: str, password: str) -> Optional[UserDB]:
        logger.debug(f"UserService.authenticate_user called with username: {username}")
        user = self.get_user_by_username(username)
        logger.debug(f"User found: {user is not None}")
        
        if not user:
            logger.warning(f"Authentication failed: user '{username}' not found")
            return None
            
        logger.debug(f"Checking password for user: {user.username}")
        password_valid = check_password_hash(user.password_hash, password)
        logger.debug(f"Password valid: {password_valid}")
        
        if not password_valid:
            logger.warning(f"Authentication failed: invalid password for user '{username}'")
            return None
            
        logger.info(f"Authentication successful for user: {user.username}")
        return user
