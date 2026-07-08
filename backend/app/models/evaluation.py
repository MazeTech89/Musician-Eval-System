"""Evaluation and performance models for database."""

from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.models.user import Base


class EvaluationStatus(str, Enum):
    """Evaluation status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AnalysisStatus(str, Enum):
    """AI analysis status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Performance(Base):
    """Performance model."""

    __tablename__ = "performances"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    audio_file_url = Column(String(500))  # URL for backward compatibility
    audio_s3_key = Column(String(500), nullable=True, unique=True)  # S3 object key
    musician_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="pending")  # pending, approved, rejected
    file_size_bytes = Column(Integer, nullable=True)  # File size in bytes
    uploaded_at = Column(DateTime, nullable=True)  # When file was uploaded

    # Relationships
    musician = relationship("User", back_populates="performances")
    evaluations = relationship("Evaluation", back_populates="performance")
    analysis = relationship(
        "PerformanceAnalysis",
        back_populates="performance",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Evaluation(Base):
    """Evaluation model."""

    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    performance_id = Column(Integer, ForeignKey("performances.id"), nullable=False)
    evaluator_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    score = Column(Float, nullable=True)  # 0-100
    comments = Column(Text)
    status = Column(SQLEnum(EvaluationStatus), default=EvaluationStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    performance = relationship("Performance", back_populates="evaluations")
    evaluator = relationship("User", back_populates="evaluations")


class PerformanceAnalysis(Base):
    """AI analysis output for a submitted performance."""

    __tablename__ = "performance_analysis"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    performance_id = Column(Integer, ForeignKey("performances.id"), nullable=False, unique=True)
    status = Column(SQLEnum(AnalysisStatus), default=AnalysisStatus.PENDING, nullable=False)
    technique_score = Column(Float, nullable=True)
    timing_score = Column(Float, nullable=True)
    intonation_score = Column(Float, nullable=True)
    overall_ai_score = Column(Float, nullable=True)
    ai_feedback = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    analyzed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    performance = relationship("Performance", back_populates="analysis")
