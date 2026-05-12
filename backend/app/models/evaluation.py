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


class Performance(Base):
    """Performance model."""

    __tablename__ = "performances"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    audio_file_url = Column(String(500))
    musician_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="pending")  # pending, approved, rejected

    # Relationships
    musician = relationship("User", back_populates="performances")
    evaluations = relationship("Evaluation", back_populates="performance")


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
