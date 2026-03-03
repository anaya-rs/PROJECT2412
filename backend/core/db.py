"""
v 1.1 core database - database connection and session management
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from .config import settings
from models.base import Base


# create database engine
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=StaticPool,
    connect_args={
        "check_same_thread": False,
        "timeout": 20
    },
    echo=False
)

# create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def init_db():
    """initialize database with all tables"""
    os.makedirs("data", exist_ok=True)
    
    # import all models to ensure they're registered
    from models.lesson import LessonDB
    from models.session import LessonSessionDB
    from models.session_runtime import LessonSessionRuntimeDB
    from models.analytics import AnalyticsEventDB
    from models.job import JobDB
    from models.user import UserDB
    
    # create all tables first   
    Base.metadata.create_all(bind=engine)
    
    # create indexes after tables exist
    with engine.connect() as conn:
        # performance indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sessions_lesson_user ON lesson_sessions(lesson_id, user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sessions_user ON lesson_sessions(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_session_runtime_lesson_id ON lesson_session_runtime(lesson_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_session_runtime_user_id ON lesson_session_runtime(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_session_runtime_started_at ON lesson_session_runtime(started_at)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_analytics_session ON analytics_events(session_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_analytics_lesson ON analytics_events(lesson_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_analytics_user ON analytics_events(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_jobs_user ON jobs(user_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)"))
    
    print("Database initialized with clean schema")


@contextmanager
def get_db():
    """get database session"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_db_session():
    """get database session (not context manager) - for compatibility"""
    return SessionLocal()
