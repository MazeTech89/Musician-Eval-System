"""Health check schemas."""

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """Health check response model.

    Attributes:
        status: Health status of the application
    """

    model_config = ConfigDict(
        json_schema_extra={"example": {"status": "ok"}},
    )

    status: str = Field(..., description="Health status")
