"""Evaluation and performance schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class PerformanceBase(BaseModel):
    """Base performance schema."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    audio_file_url: str | None = None


class PerformanceCreate(PerformanceBase):
    """Performance creation schema."""

    pass


class PerformanceUpdate(BaseModel):
    """Performance update schema."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    audio_file_url: str | None = None
    status: str | None = None


class PerformanceResponse(PerformanceBase):
    """Performance response schema."""

    id: int
    musician_id: int
    submitted_at: datetime
    status: str

    class Config:
        from_attributes = True


class EvaluationBase(BaseModel):
    """Base evaluation schema."""

    performance_id: int
    score: float | None = Field(None, ge=0, le=100)
    comments: str | None = Field(None, max_length=1000)


class EvaluationCreate(EvaluationBase):
    """Evaluation creation schema."""

    pass


class EvaluationUpdate(BaseModel):
    """Evaluation update schema."""

    score: float | None = Field(None, ge=0, le=100)
    comments: str | None = Field(None, max_length=1000)
    status: str | None = None


class EvaluationResponse(EvaluationBase):
    """Evaluation response schema."""

    id: int
    evaluator_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EvaluationWithPerformanceResponse(EvaluationResponse):
    """Evaluation response with performance details."""

    performance: PerformanceResponse

    class Config:
        from_attributes = True
