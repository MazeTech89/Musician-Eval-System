"""Security utilities for JWT and password handling."""

from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from jose import JWTError, jwt

from app.core.config import settings
from app.schemas.auth import TokenData

# Password hashing
password_hasher = PasswordHasher()


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
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        user_id = payload.get("sub")
        username: str = payload.get("username")
        role: str = payload.get("role")

        if isinstance(user_id, str) and user_id.isdigit():
            user_id = int(user_id)

        if user_id is None or username is None or role is None:
            return None

        return TokenData(
            sub=user_id,
            username=username,
            role=role,
        )
    except JWTError:
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
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )

        # Verify token type
        token_type = payload.get("type")
        if token_type != "refresh":
            return None

        user_id = payload.get("sub")
        username: str = payload.get("username")
        role: str = payload.get("role")

        if isinstance(user_id, str) and user_id.isdigit():
            user_id = int(user_id)

        if user_id is None or username is None or role is None:
            return None

        return TokenData(
            sub=user_id,
            username=username,
            role=role,
        )
    except JWTError:
        return None
