"""Database configuration and session management."""

from sqlalchemy import create_engine, inspect, text
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


def _ensure_schema_columns() -> None:
    """Add missing columns for newer model fields to existing databases."""
    from app.models.evaluation import Performance
    from app.models.reference_track import Assignment, ReferenceTrack

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    tables = [ReferenceTrack.__table__, Assignment.__table__, Performance.__table__]

    for table in tables:
        if table.name not in existing_tables:
            continue

        existing_columns = {column["name"] for column in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in existing_columns:
                continue

            column_type = column.type.compile(dialect=engine.dialect)
            with engine.begin() as connection:
                connection.execute(
                    text(
                        f"ALTER TABLE {table.name} ADD COLUMN IF NOT EXISTS "
                        f"{column.name} {column_type}"
                    )
                )

        for column in inspector.get_columns(table.name):
            if column["name"] in table.columns.keys():
                continue
            if not column["nullable"]:
                with engine.begin() as connection:
                    connection.execute(
                        text(
                            f"ALTER TABLE {table.name} ALTER COLUMN {column['name']} "
                            "DROP NOT NULL"
                        )
                    )

        if "is_active" in existing_columns and table.name in {"reference_tracks", "assignments"}:
            with engine.begin() as connection:
                connection.execute(
                    text(f"UPDATE {table.name} SET is_active = TRUE WHERE is_active IS NULL")
                )


def init_db() -> None:
    """Initialize database by creating all tables."""
    from app.models.evaluation import Evaluation, Performance  # noqa: F401
    from app.models.reference_track import Assignment, ReferenceTrack  # noqa: F401
    from app.models.user import Base

    Base.metadata.create_all(bind=engine)
    _ensure_schema_columns()
