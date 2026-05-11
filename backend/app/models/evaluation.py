"""Evaluation and performance models for database."""

from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.models.user import Base


class EvaluationStatus(str, Enum):
    """Evaluation status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Performance(Base):
    """Performance model."""

    __tablename__ = "performances"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    audio_file_url = Column(String)
    musician_id = Column(String, ForeignKey("users.id"), nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")  # pending, approved, rejected

    # Relationships
    musician = relationship("User", back_populates="performances")
    evaluations = relationship("Evaluation", back_populates="performance")


class Evaluation(Base):
    """Evaluation model."""

    __tablename__ = "evaluations"

    id = Column(String, primary_key=True, index=True)
    performance_id = Column(String, ForeignKey("performances.id"), nullable=False)
    evaluator_id = Column(String, ForeignKey("users.id"), nullable=False)
    score = Column(Float, nullable=True)  # 0-100
    comments = Column(Text)
    status = Column(SQLEnum(EvaluationStatus), default=EvaluationStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    performance = relationship("Performance", back_populates="evaluations")
    evaluator = relationship("User", back_populates="evaluations")
