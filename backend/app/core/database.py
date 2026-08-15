"""Database configuration and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

# Create database engine
engine_kwargs: dict = {
    "echo": settings.debug,
}

if settings.database_url.startswith("sqlite"):
    # SQLite is used in tests; this avoids cross-thread connection errors in TestClient.
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    if settings.database_url.endswith(":memory:"):
        engine_kwargs["poolclass"] = StaticPool
else:
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_engine(settings.database_url, **engine_kwargs)

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
    from app.models.evaluation import Evaluation, Performance  # noqa: F401
    from app.models.user import Base

    Base.metadata.create_all(bind=engine)

    # Seed roles and permissions
    db = SessionLocal()
    try:
        init_roles_and_permissions(db)
    finally:
        db.close()
