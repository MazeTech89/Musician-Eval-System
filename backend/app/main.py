"""FastAPI application factory and configuration."""

import os
from collections import defaultdict
from pathlib import Path
from threading import Lock
from time import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1 import router as api_v1_router
from app.core.audit import record_security_alert
from app.core.config import settings
from app.core.database import init_db
from app.core.exceptions import register_exception_handlers

# In-memory sliding-window rate limiter state: only viable for a single process/worker,
# resets on restart. Good enough for this deployment's scale (no shared Redis limiter yet).
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 10
request_log: dict[str, list[float]] = defaultdict(list)
request_lock = Lock()


def _get_client_ip(request: Request) -> str:
    # Render/most PaaS proxies sit in front of the app, so the real client IP arrives via
    # X-Forwarded-For rather than the raw socket address.
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Cache-Control"] = "no-store"
    # connect-src whitelists both local dev and the deployed Render backend so the frontend
    # can call the API under CSP in every environment without loosening it to '*'.
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; "
        "font-src 'self' data:; connect-src 'self' http://localhost:8000 https://musician-eval-backend.onrender.com; "  # noqa: E501
        "object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    )
    if not settings.debug:
        # HSTS only makes sense once TLS is actually terminated in front of the app (prod/Render).
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


async def rate_limit_middleware(request: Request, call_next):
    # Only auth endpoints are rate-limited: these are the brute-force/credential-stuffing targets.
    if not request.url.path.startswith("/api/v1/auth"):
        return await call_next(request)

    # Bypass in debug/dev and during pytest runs so local development and test suites aren't
    # throttled by a limiter meant for production abuse protection.
    if settings.debug or os.getenv("PYTEST_CURRENT_TEST"):
        return await call_next(request)

    key = _get_client_ip(request)
    now = time()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS
    with request_lock:
        requests = request_log[key]
        # Drop timestamps outside the sliding window before counting/appending.
        request_log[key] = [timestamp for timestamp in requests if timestamp >= window_start]
        if len(request_log[key]) >= RATE_LIMIT_MAX_REQUESTS:
            record_security_alert(
                "auth.rate_limited",
                ip=key,
                path=request.url.path,
            )
            return JSONResponse(status_code=429, content={"detail": "Too many requests"})
        request_log[key].append(now)
    return await call_next(request)


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

    # Creates tables via metadata.create_all + adds any new nullable columns (no Alembic here).
    init_db()

    # Register exception handlers
    register_exception_handlers(app)

    # Starlette applies middleware in reverse registration order, so rate limiting runs
    # before security headers are attached to the (possibly 429) response.
    app.middleware("http")(rate_limit_middleware)
    app.middleware("http")(security_headers_middleware)

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Local-disk upload fallback (used when S3 env vars aren't configured) is served as static
    # files so the frontend can render/play uploaded audio directly from this path.
    upload_dir = Path(settings.local_upload_dir)
    if not upload_dir.is_absolute():
        upload_dir = Path.cwd() / upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

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
