"""API v1 routes."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.evaluations import router as evaluations_router
from app.api.v1.health import router as health_router
from app.api.v1.users import router as users_router

router = APIRouter(prefix="/api/v1", tags=["v1"])

router.include_router(auth_router)
router.include_router(evaluations_router)
router.include_router(health_router)
router.include_router(users_router)

__all__ = ["router"]
