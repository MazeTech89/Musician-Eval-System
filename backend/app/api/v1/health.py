"""Health check endpoints."""

from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse, status_code=200)
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        HealthResponse: Application health status

    Raises:
        None

    Example:
        GET /api/v1/health
        Response: {"status": "ok"}
    """
    return HealthResponse(status="ok")
