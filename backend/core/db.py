"""
Core Database - Database connection and session management
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from models.base import Base


# Create database engine
engine = create_engine(
    "sqlite:///data/lessons.db",
    poolclass=StaticPool,
    connect_args={
        "check_same_thread": False,
        "timeout": 20
    },
    echo=False
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def init_db():
    """Initialize database with all tables"""
    os.makedirs("data", exist_ok=True)
    
    # Import all models to ensure they're registered
    from models.lesson import LessonDB
    from models.session import LessonSessionDB
    from models.analytics import AnalyticsEventDB
    
    # Create all tables first
    Base.metadata.create_all(bind=engine)
    
    # Create indexes after tables exist
    with engine.connect() as conn:
        # Performance indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sessions_lesson_user ON lesson_sessions(lesson_id, user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sessions_user ON lesson_sessions(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_analytics_session ON analytics_events(session_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_analytics_lesson ON analytics_events(lesson_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_analytics_user ON analytics_events(user_id)"))
    
    print("Database initialized with clean schema")


@contextmanager
def get_db():
    """Get database session"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    
    # Create job table if it doesn't exist
    from models.job import JobDB
    JobDB.metadata.create_all(engine)
    
    session = Session()
    try:
        yield session
    finally:
        session.close()


def get_db_session():
    """Get database session (not context manager) - for compatibility"""
    return SessionLocal()
