"""Request and response schemas."""

from app.schemas.health import HealthResponse
from app.schemas.challenge import (
    AnalysisResultResponse,
    AssignmentCreate,
    AssignmentResponse,
    AssignmentUpdate,
    ReferenceTrackCreate,
    ReferenceTrackResponse,
    SubmissionResponse,
)

__all__ = [
    "HealthResponse",
    "ReferenceTrackCreate",
    "ReferenceTrackResponse",
    "AssignmentCreate",
    "AssignmentResponse",
    "AssignmentUpdate",
    "AnalysisResultResponse",
    "SubmissionResponse",
]
