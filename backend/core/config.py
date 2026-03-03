"""
v 1.1 core configuration - application settings
"""

import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

class SimpleSettings:
    """Simple settings class without pydantic"""
    
    def __init__(self):
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/lessons.db")
        self.API_PREFIX = os.getenv("API_PREFIX", "/api")
        self.DEBUG = os.getenv("DEBUG", "False").lower() == "true"
        self.JWT_SECRET = os.getenv("JWT_SECRET", "test-secret-key-change-in-production")

# Global settings instance
settings = SimpleSettings()

def get_settings():
    """Get application settings"""
    return settings
