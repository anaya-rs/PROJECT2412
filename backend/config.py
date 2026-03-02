"""
application configuration
"""

from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # database
    database_url: str = "sqlite:///data/lessons.db"
    
    # jwt
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours
    
    # ollama
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:1.5b"
    
    # openai
    openai_api_key: Optional[str] = None
    
    # logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # ignore extra environment variables


settings = Settings()
