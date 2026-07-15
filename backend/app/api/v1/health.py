"""Health check endpoints."""

from fastapi import APIRouter, Request

from app.core.rate_limit import limiter
from app.schemas.health import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse, status_code=200)
@limiter.limit("300/minute")  # Allow frequent health checks (300 per minute)
async def health_check(request: Request) -> HealthResponse:
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
