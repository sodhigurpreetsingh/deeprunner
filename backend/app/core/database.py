"""Database connection and session management"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from app.core.config import settings

# Base class for models
Base = declarative_base()

# Sync engine for database operations
sync_engine = create_engine(
    settings.postgres_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Export for use in other modules
__all__ = ['Base', 'sync_engine', 'get_sync_db', 'get_db']


def get_sync_db() -> Session:
    """Get synchronous database session (for Celery workers)"""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db() -> Session:
    """Get database session for FastAPI dependency injection"""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()
