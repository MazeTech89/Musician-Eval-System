"""Rate limiting configuration for FastAPI application."""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

# Initialize rate limiter using IP address as key
limiter = Limiter(key_func=get_remote_address)

# Rate limit constants
AUTH_LIMIT = (
    "1000/minute" if settings.environment == "test" else "5/minute"
)  # Login/register attempts
UPLOAD_LIMIT = "30/minute"  # File uploads: 30 per minute
API_LIMIT = "100/minute"  # General API calls: 100 per minute
STRICT_LIMIT = "1/second"  # Very strict for sensitive operations: 1 per second

# Rate limit names for decorators
AUTH_RATE_LIMIT = AUTH_LIMIT
UPLOAD_RATE_LIMIT = UPLOAD_LIMIT
API_RATE_LIMIT = API_LIMIT
STRICT_RATE_LIMIT = STRICT_LIMIT
