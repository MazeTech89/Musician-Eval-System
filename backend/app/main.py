"""FastAPI application factory and configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as api_v1_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )

    # Register exception handlers
    register_exception_handlers(app)

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Include API routers
    app.include_router(api_v1_router)

    # Root endpoint
    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint.

        Returns:
            dict: Application information
        """
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "running",
        }

    return app


app = create_app()
