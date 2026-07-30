"""Schemas for reference tracks, assignments, submissions, and analysis."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReferenceTrackBase(BaseModel):
    """Base reference track schema."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)


class ReferenceTrackCreate(ReferenceTrackBase):
    """Reference track creation schema."""

    pass


class ReferenceTrackResponse(ReferenceTrackBase):
    """Reference track response schema."""

    id: int
    audio_file_url: str
    uploaded_by_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssignmentBase(BaseModel):
    """Base assignment schema."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    reference_track_id: int
    target_role: str = Field(default="musician", max_length=50)
    due_at: datetime | None = None
    is_active: bool = True


class AssignmentCreate(AssignmentBase):
    """Assignment creation schema."""

    pass


class AssignmentUpdate(BaseModel):
    """Assignment update schema."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    reference_track_id: int | None = None
    target_role: str | None = Field(default=None, max_length=50)
    due_at: datetime | None = None
    is_active: bool | None = None


class AssignmentResponse(AssignmentBase):
    """Assignment response schema."""

    id: int
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    reference_track: ReferenceTrackResponse

    model_config = ConfigDict(from_attributes=True)


class AnalysisResultResponse(BaseModel):
    """Analysis result response schema."""

    id: int
    submission_id: int
    reference_track_id: int
    similarity_score: float
    model_version: str
    metrics_json: str | None = None
    summary: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class SubmissionResponse(BaseModel):
    """Submission response schema."""

    id: int
    assignment_id: int
    musician_id: int
    audio_file_url: str
    notes: str | None = None
    status: str
    similarity_score: float | None = None
    analyzed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    assignment: AssignmentResponse
    analysis_result: AnalysisResultResponse | None = None

    model_config = ConfigDict(from_attributes=True)
