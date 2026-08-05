"""Database configuration and session management."""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Create database engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,  # Log generated SQL when running in debug mode
    pool_pre_ping=True,  # Verify connections are alive before use (avoids stale connection errors)
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
        # Always release the connection back to the pool, even on error
        db.close()


def _ensure_schema_columns() -> None:
    """Add missing columns for newer model fields to existing databases."""
    from app.models.evaluation import Performance
    from app.models.reference_track import Assignment, ReferenceTrack
    from app.models.user import User

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    tables = [ReferenceTrack.__table__, Assignment.__table__, Performance.__table__, User.__table__]

    def quote_identifier(name: str) -> str:
        # Quote identifiers so reserved words like "user" are valid in raw SQL
        return f'"{name}"'

    for table in tables:
        if table.name not in existing_tables:
            # Table doesn't exist yet; create_all() will handle it, nothing to migrate
            continue

        existing_columns = {column["name"] for column in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in existing_columns:
                continue

            # Model has a column the DB table doesn't; add it on the fly (lightweight migration)
            column_type = column.type.compile(dialect=engine.dialect)
            with engine.begin() as connection:
                quoted_table = quote_identifier(table.name)
                quoted_column = quote_identifier(column.name)
                connection.execute(
                    text(
                        f"ALTER TABLE {quoted_table} ADD COLUMN IF NOT EXISTS "
                        f"{quoted_column} {column_type}"
                    )
                )

        for column in inspector.get_columns(table.name):
            if column["name"] in table.columns.keys():
                continue
            if not column["nullable"]:
                # Column was removed from the model but still required in the DB;
                # relax the constraint so inserts from the current model don't fail
                with engine.begin() as connection:
                    quoted_table = quote_identifier(table.name)
                    quoted_column = quote_identifier(column["name"])
                    connection.execute(
                        text(
                            f"ALTER TABLE {quoted_table} ALTER COLUMN {quoted_column} "
                            "DROP NOT NULL"
                        )
                    )

        if "is_active" in existing_columns and table.name in {"reference_tracks", "assignments"}:
            # Backfill newly added is_active flag so existing rows remain visible/active
            with engine.begin() as connection:
                quoted_table = quote_identifier(table.name)
                connection.execute(
                    text(f"UPDATE {quoted_table} SET is_active = TRUE WHERE is_active IS NULL")
                )

    if "user" in existing_tables:
        # Backfill defaults for security-related columns added after initial rollout
        with engine.begin() as connection:
            quoted_user_table = quote_identifier("user")
            connection.execute(
                text(
                    f"UPDATE {quoted_user_table} SET email_verified = TRUE WHERE email_verified IS NULL"
                )
            )
            connection.execute(
                text(
                    f"UPDATE {quoted_user_table} SET mfa_enabled = FALSE WHERE mfa_enabled IS NULL"
                )
            )
            connection.execute(
                text(
                    f"UPDATE {quoted_user_table} SET failed_login_count = 0 WHERE failed_login_count IS NULL"
                )
            )


def init_db() -> None:
    """Initialize database by creating all tables."""
    from app.models.evaluation import Evaluation, Performance  # noqa: F401
    from app.models.reference_track import Assignment, ReferenceTrack  # noqa: F401
    from app.models.user import Base

    Base.metadata.create_all(bind=engine)
    _ensure_schema_columns()
