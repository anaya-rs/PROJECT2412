"""
v 1.1 core configuration - application settings
"""

import os
from dotenv import load_dotenv
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """application settings"""
    
    # openai settings
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    
    #  database settings
    DATABASE_URL: str = "sqlite:///data/lessons.db"
    
    # api settings
    API_PREFIX: str = "/api"
    DEBUG: bool = False
    
    # jwt settings
    secret_key: str = "test-secret-key-change-in-production"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  


# global settings instance
settings = Settings()


def get_settings() -> Settings:
    """get application settings"""
    return settings


# load environment variables
load_dotenv()
