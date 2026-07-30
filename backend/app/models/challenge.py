"""Reference track, assignment, submission, and analysis models."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.user import Base


class ReferenceTrack(Base):
    """Admin-uploaded original song."""

    __tablename__ = "reference_tracks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    audio_file_url = Column(String(500), nullable=False)
    uploaded_by_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    uploaded_by = relationship("User", back_populates="reference_tracks")
    assignments = relationship("Assignment", back_populates="reference_track")


class Assignment(Base):
    """A challenge tied to a reference track."""

    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    reference_track_id = Column(
        Integer, ForeignKey("reference_tracks.id"), nullable=False, index=True
    )
    created_by_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    target_role = Column(String(50), nullable=False, default="musician")
    due_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    reference_track = relationship("ReferenceTrack", back_populates="assignments")
    created_by = relationship("User", back_populates="created_assignments")
    submissions = relationship("Submission", back_populates="assignment")


class Submission(Base):
    """Musician recording uploaded against an assignment."""

    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False, index=True)
    musician_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    audio_file_url = Column(String(500), nullable=False)
    notes = Column(Text)
    status = Column(String(50), default="pending_analysis", nullable=False)
    similarity_score = Column(Float, nullable=True)
    analyzed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    assignment = relationship("Assignment", back_populates="submissions")
    musician = relationship("User", back_populates="submissions")
    analysis_result = relationship("AnalysisResult", back_populates="submission", uselist=False)


class AnalysisResult(Base):
    """Computed similarity output for a submission."""

    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), unique=True, nullable=False)
    reference_track_id = Column(
        Integer, ForeignKey("reference_tracks.id"), nullable=False, index=True
    )
    similarity_score = Column(Float, nullable=False)
    model_version = Column(String(50), nullable=False, default="phase1-placeholder")
    metrics_json = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    submission = relationship("Submission", back_populates="analysis_result")
    reference_track = relationship("ReferenceTrack")
