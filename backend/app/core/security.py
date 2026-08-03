"""Security utilities for JWT and password handling."""

from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi.responses import Response
from jwt.exceptions import InvalidTokenError

from app.core.config import settings
from app.schemas.auth import TokenData

# Password hashing
password_hasher = PasswordHasher()
REFRESH_TOKEN_TYPE = "refresh"


def _get_secret_keys() -> list[str]:
    keys = [settings.secret_key]
    if settings.secret_key_fallbacks.strip():
        keys.extend(
            key.strip()
            for key in settings.secret_key_fallbacks.split(",")
            if key.strip()
        )
    return keys


def hash_password(password: str) -> str:
    """Hash a password using Argon2id.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: The hash to verify against

    Returns:
        True if password matches, False otherwise
    """
    try:
        password_hasher.verify(hashed_password, plain_password)
        return True
    except (VerifyMismatchError, InvalidHashError):
        return False


# JWT token handling
def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> tuple[str, datetime]:
    """Create a JWT access token.

    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta

    Returns:
        Tuple of (token, expiration_datetime)
    """
    to_encode = data.copy()

    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    return encoded_jwt, expire


def decode_token(token: str) -> TokenData | None:
    """Decode and validate a JWT token.

    Args:
        token: JWT token to decode

    Returns:
        TokenData if valid, None otherwise
    """
    for secret_key in _get_secret_keys():
        try:
            payload = jwt.decode(
                token,
                secret_key,
                algorithms=[settings.algorithm],
            )
        except InvalidTokenError:
            continue

        user_id = payload.get("sub")
        username: str = payload.get("username")
        role: str = payload.get("role")

        if isinstance(user_id, str) and user_id.isdigit():
            user_id = int(user_id)

        if user_id is None or username is None or role is None:
            return None

        return TokenData(sub=user_id, username=username, role=role)

    return None


def create_refresh_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> tuple[str, datetime]:
    """Create a JWT refresh token.

    Refresh tokens have a longer expiration than access tokens
    and are used to obtain new access tokens without re-authentication.

    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta

    Returns:
        Tuple of (token, expiration_datetime)
    """
    to_encode = data.copy()

    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        # Refresh token expires in 7 days
        expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)

    to_encode.update({"exp": expire, "type": "refresh"})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    return encoded_jwt, expire


def decode_refresh_token(token: str) -> TokenData | None:
    """Decode and validate a refresh JWT token.
    
    Args:
        token: Refresh JWT token to decode
    
    Returns:
        TokenData if valid, None otherwise
    """
    for secret_key in _get_secret_keys():
        try:
            payload = jwt.decode(
                token,
                secret_key,
                algorithms=[settings.algorithm],
            )
        except InvalidTokenError:
            continue

        # Verify token type
        payload_token_type = payload.get("type")
        if payload_token_type != REFRESH_TOKEN_TYPE:
            return None

        user_id = payload.get("sub")
        username: str = payload.get("username")
        role: str = payload.get("role")

        if isinstance(user_id, str) and user_id.isdigit():
            user_id = int(user_id)

        if user_id is None or username is None or role is None:
            return None

        return TokenData(sub=user_id, username=username, role=role)

    return None


def set_auth_cookies(response: Response, access_token: str, refresh_token: str | None = None) -> None:
    """Set auth cookies for the browser using HttpOnly cookies."""
    secure = not settings.debug
    samesite = "none" if not settings.debug else "lax"
    response.set_cookie(
        key=settings.access_token_cookie_name,
        value=access_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path="/",
        max_age=settings.access_token_expire_minutes * 60,
    )
    if refresh_token:
        response.set_cookie(
            key=settings.refresh_token_cookie_name,
            value=refresh_token,
            httponly=True,
            secure=secure,
            samesite=samesite,
            path="/",
            max_age=settings.refresh_token_expire_days * 86400,
        )


def clear_auth_cookies(response: Response) -> None:
    """Clear auth cookies from the browser."""
    secure = not settings.debug
    samesite = "none" if not settings.debug else "lax"
    for cookie_name in (settings.access_token_cookie_name, settings.refresh_token_cookie_name):
        response.delete_cookie(cookie_name, path="/", secure=secure, samesite=samesite)
