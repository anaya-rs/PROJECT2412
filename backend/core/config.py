"""
Core Configuration - Application settings
"""

import os
from dotenv import load_dotenv
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Ollama settings
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:latest"
    
    # Database settings
    DATABASE_URL: str = "sqlite:///data/lessons.db"
    
    # API settings
    API_PREFIX: str = "/api"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings


# Load environment variables
load_dotenv()

# Print settings on startup
if __name__ != "__main__":
    print(f"Settings initialized:")
    print(f"  OLLAMA_URL: {settings.OLLAMA_URL}")
    print(f"  OLLAMA_MODEL: {settings.OLLAMA_MODEL}")
    print(f"  DATABASE_URL: {settings.DATABASE_URL}")
