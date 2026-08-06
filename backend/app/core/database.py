"""Database configuration and session management."""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Create database engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,  # validates connections before use so recycled/dropped DB connections
    # (common on managed Postgres after idle periods) don't surface as request failures.
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
    # This project has no Alembic migrations: schema changes ship as new nullable model
    # columns, and this function reconciles an already-deployed DB with the current models
    # by diffing SQLAlchemy metadata against `information_schema` and running ALTER TABLE.
    from app.models.evaluation import Performance
    from app.models.reference_track import Assignment, ReferenceTrack
    from app.models.user import User

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    tables = [ReferenceTrack.__table__, Assignment.__table__, Performance.__table__, User.__table__]

    def quote_identifier(name: str) -> str:
        return f'"{name}"'

    for table in tables:
        if table.name not in existing_tables:
            continue

        existing_columns = {column["name"] for column in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in existing_columns:
                continue

            # Table/column names come from trusted SQLAlchemy model metadata (not request
            # input), so string-built DDL here isn't a SQL-injection vector.
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
                # A column that exists in the DB but not in current models, and is NOT NULL,
                # would block inserts from the new model — relax it rather than fail writes.
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
            # Backfill newly-added is_active column on pre-existing rows so old data doesn't
            # silently disappear from "active" filters after the column was introduced.
            with engine.begin() as connection:
                quoted_table = quote_identifier(table.name)
                connection.execute(
                    text(f"UPDATE {quoted_table} SET is_active = TRUE WHERE is_active IS NULL")  # noqa: S608  # nosec B608
                )

    if "user" in existing_tables:
        # Same backfill pattern for user-table columns added after initial deployment.
        with engine.begin() as connection:
            quoted_user_table = quote_identifier("user")
            connection.execute(
                text(
                    f"UPDATE {quoted_user_table} SET email_verified = TRUE WHERE email_verified IS NULL"  # noqa: S608, E501  # nosec B608
                )
            )
            connection.execute(
                text(
                    f"UPDATE {quoted_user_table} SET mfa_enabled = FALSE WHERE mfa_enabled IS NULL"  # noqa: S608  # nosec B608
                )
            )
            connection.execute(
                text(
                    f"UPDATE {quoted_user_table} SET failed_login_count = 0 WHERE failed_login_count IS NULL"  # noqa: S608, E501  # nosec B608
                )
            )


def init_db() -> None:
    """Initialize database by creating all tables."""
    from app.models.evaluation import Evaluation, Performance  # noqa: F401
    from app.models.reference_track import Assignment, ReferenceTrack  # noqa: F401
    from app.models.user import Base

    # create_all only adds brand-new tables; it never alters existing ones, hence the
    # follow-up _ensure_schema_columns() call to patch columns onto already-deployed tables.
    Base.metadata.create_all(bind=engine)
    _ensure_schema_columns()
