"""Reference track and assignment models for persistent evaluation workflows."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.user import Base


class ReferenceTrack(Base):
    """Reusable reference audio for evaluation assignments."""

    __tablename__ = "reference_tracks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    audio_file_url = Column(String(500), nullable=False)
    created_by_id = Column("uploaded_by_id", Integer, ForeignKey("user.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True, nullable=False)

    created_by = relationship("User", foreign_keys=[created_by_id])
    assignments = relationship(
        "Assignment",
        back_populates="reference_track",
        cascade="all, delete-orphan",
    )


class Assignment(Base):
    """An evaluation assignment that binds a performance to a reusable reference track."""

    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    reference_track_id = Column(Integer, ForeignKey("reference_tracks.id"), nullable=False)
    created_by_id = Column("created_by_id", Integer, ForeignKey("user.id"), nullable=False)
    # Null targeting fields mean the task is open to every musician.
    target_musician_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    target_instrument_type = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True, nullable=False)

    reference_track = relationship("ReferenceTrack", back_populates="assignments")
    created_by = relationship("User", foreign_keys=[created_by_id])
    target_musician = relationship("User", foreign_keys=[target_musician_id])
    performances = relationship("Performance", back_populates="assignment")
