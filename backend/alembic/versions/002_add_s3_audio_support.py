"""
Database migration for adding S3 audio storage support.

Adds columns to Performance model to track S3 keys and file metadata.
"""

import sqlalchemy as sa
from alembic import op

# Alembic migration version
revision = '002_add_s3_audio_support'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    """Add S3 audio support columns to performances table."""
    # Add S3 key column
    op.add_column(
        'performances',
        sa.Column('audio_s3_key', sa.String(500), nullable=True, unique=True)
    )
    
    # Add file metadata columns
    op.add_column(
        'performances',
        sa.Column('file_size_bytes', sa.Integer(), nullable=True)
    )
    
    # Add upload timestamp
    op.add_column(
        'performances',
        sa.Column('uploaded_at', sa.DateTime(), nullable=True)
    )
    
    # Create index on S3 key for faster lookups
    op.create_index('ix_performances_audio_s3_key', 'performances', ['audio_s3_key'])


def downgrade():
    """Remove S3 audio support columns from performances table."""
    # Drop index
    op.drop_index('ix_performances_audio_s3_key', 'performances')
    
    # Drop columns
    op.drop_column('performances', 'uploaded_at')
    op.drop_column('performances', 'file_size_bytes')
    op.drop_column('performances', 'audio_s3_key')
