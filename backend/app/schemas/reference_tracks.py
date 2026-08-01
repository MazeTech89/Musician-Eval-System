"""Schemas for reusable reference tracks and assignments."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.evaluation import (
    EvaluationResponse,
    PerformanceResponse,
    SimilarityAnalysisResponse,
)


class ReferenceTrackBase(BaseModel):
    """Base schema for reference tracks."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    is_active: bool = True


class ReferenceTrackCreate(ReferenceTrackBase):
    """Schema for creating a reference track."""

    pass


class ReferenceTrackUpdate(BaseModel):
    """Schema for updating a reference track."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    is_active: bool | None = None


class ReferenceTrackResponse(ReferenceTrackBase):
    """Response schema for a reference track."""

    id: int
    audio_file_url: str
    created_by_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssignmentBase(BaseModel):
    """Base schema for assignments."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    reference_track_id: int
    is_active: bool = True


class AssignmentCreate(AssignmentBase):
    """Schema for creating an assignment."""

    pass


class AssignmentUpdate(BaseModel):
    """Schema for updating an assignment."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    reference_track_id: int | None = None
    is_active: bool | None = None


class AssignmentResponse(AssignmentBase):
    """Response schema for an assignment."""

    id: int
    created_by_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssignmentWithReferenceResponse(AssignmentResponse):
    """Assignment response with nested reference track details."""

    reference_track: ReferenceTrackResponse

    class Config:
        from_attributes = True


class AssignmentSubmissionResponse(BaseModel):
    """Response for a musician submission against an assignment."""

    performance: PerformanceResponse
    evaluation: EvaluationResponse
    analysis: SimilarityAnalysisResponse | None = None
    message: str | None = None
