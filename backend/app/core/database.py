"""Database configuration and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Create database engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Session:
    """Get database session.

    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database by creating all tables and seeding default data."""
    from app.core.init_db import init_roles_and_permissions
    from app.models.evaluation import Evaluation, Performance, PerformanceAnalysis  # noqa: F401
    from app.models.user import Base

    Base.metadata.create_all(bind=engine)

    # Seed roles and permissions
    db = SessionLocal()
    try:
        init_roles_and_permissions(db)
    finally:
        db.close()
