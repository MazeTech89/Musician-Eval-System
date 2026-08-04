"""Authentication API routes."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.audit import record_audit_event
from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_current_admin
from app.core.security import clear_auth_cookies, set_auth_cookies
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    MFASetupResponse,
    MFAVerifyRequest,
    PasswordChangeRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Register a new user.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        Created user

    Raises:
        HTTPException: If user already exists or role is invalid
    """
    try:
        # AuthService centralizes validation (duplicates, role checks, password hashing).
        user = AuthService.register_user(db, user_data)
        # Every auth boundary action is audited for traceability and security reviews.
        record_audit_event(
            "auth.register.request",
            username=user.username,
            role=user.role.name.value,
            ip=request.client.host if request.client else None,
        )
        return user
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Login and get access token.

    Args:
        credentials: Login credentials
        db: Database session

    Returns:
        Access token

    Raises:
        HTTPException: If credentials are invalid
    """
    # Validate credentials (+ optional TOTP) and issue signed access/refresh tokens.
    token = AuthService.authenticate_user(
        db,
        credentials.username,
        credentials.password,
        totp_code=credentials.totp_code,
    )

    if not token:
        record_audit_event(
            "auth.login.request_failed",
            username=credentials.username,
            ip=request.client.host if request.client else None,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password or MFA code",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Keep browser session state in secure cookies to protect protected routes.
    set_auth_cookies(response, token.access_token, token.refresh_token)
    record_audit_event(
        "auth.login.request_succeeded",
        username=credentials.username,
        ip=request.client.host if request.client else None,
    )
    return token


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    payload: RefreshTokenRequest | None = None,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Refresh access token using refresh token.

    Args:
        request: Refresh token request
        db: Database session

    Returns:
        New access token

    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    # Accept refresh token from JSON payload or cookie to support API + browser flows.
    refresh_token_value = None
    if payload and payload.refresh_token:
        refresh_token_value = payload.refresh_token
    elif request.cookies.get("refresh_token"):
        refresh_token_value = request.cookies.get("refresh_token")

    token = AuthService.refresh_access_token(db, refresh_token_value or "")

    if not token:
        record_audit_event(
            "auth.refresh.request_failed",
            ip=request.client.host if request.client else None,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Rotate cookies on refresh so client state always tracks latest token pair.
    set_auth_cookies(response, token.access_token, token.refresh_token)
    record_audit_event(
        "auth.refresh.request_succeeded",
        ip=request.client.host if request.client else None,
    )
    return token


@router.post("/logout")
async def logout(request: Request, response: Response) -> dict[str, str]:
    """Clear browser auth cookies."""
    clear_auth_cookies(response)
    record_audit_event(
        "auth.logout",
        ip=request.client.host if request.client else None,
    )
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get current user information.

    Args:
        current_user: Current authenticated user

    Returns:
        Current user information
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> User:
    """Update current user information.

    Args:
        user_data: User update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user

    Raises:
        HTTPException: If update fails
    """
    try:
        # Regular users can only update their own email and names
        if user_data.role and user_data.role != current_user.role.name:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change your own role",
            )

        # Profile updates feed later task allocation signals (instrument/skill/availability).
        user = AuthService.update_user(db, current_user, user_data)
        record_audit_event(
            "auth.profile.updated",
            user_id=current_user.id,
            username=current_user.username,
        )
        return user
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err


@router.post("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)) -> dict[str, str]:
    """Verify an email address using a verification token."""
    # Token-based verification closes the loop for registration trust checks.
    if AuthService.verify_email(db, token):
        record_audit_event("auth.email_verified.request")
        return {"message": "Email verified successfully"}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token"
    )  # noqa: E501


@router.post("/password-reset/request")
async def request_password_reset(
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Request a password reset email."""
    # Deliberately returns a generic message to avoid account enumeration leaks.
    AuthService.request_password_reset(db, payload.email)
    record_audit_event("auth.password_reset.requested.request", email=payload.email)
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    payload: PasswordResetConfirmRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Reset a password using a token."""
    # Reset is only accepted with a valid, non-expired one-time token.
    if AuthService.reset_password(db, payload.token, payload.new_password):
        record_audit_event("auth.password_reset.completed.request")
        return {"message": "Password reset successfully"}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired password reset token"
    )  # noqa: E501


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> MFASetupResponse:
    """Generate an MFA secret for the current user."""
    # MFA setup returns secret + otpauth URI used by authenticator apps.
    secret, otpauth_url = AuthService.setup_mfa(db, current_user)
    record_audit_event(
        "auth.mfa.setup.request", user_id=current_user.id, username=current_user.username
    )  # noqa: E501
    return MFASetupResponse(secret=secret, otpauth_url=otpauth_url)


@router.post("/mfa/enable")
async def enable_mfa(
    payload: MFAVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Enable MFA for the current user."""
    # Enabling MFA requires a valid code generated from the just-enrolled secret.
    if AuthService.enable_mfa(db, current_user, payload.code):
        record_audit_event(
            "auth.mfa.enable.request", user_id=current_user.id, username=current_user.username
        )  # noqa: E501
        return {"message": "MFA enabled successfully"}
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code")


@router.post("/mfa/disable")
async def disable_mfa(
    payload: MFAVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Disable MFA for the current user."""
    # Disable is protected by a live MFA code to prevent unauthorized account takeover.
    if AuthService.disable_mfa(db, current_user, payload.code):
        record_audit_event(
            "auth.mfa.disable.request", user_id=current_user.id, username=current_user.username
        )  # noqa: E501
        return {"message": "MFA disabled successfully"}
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code")


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict:
    """Change current user password.

    Args:
        password_data: Password change data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If password change fails
    """
    try:
        # Password change validates the current password and applies policy checks.
        AuthService.change_password(
            db,
            current_user,
            password_data.current_password,
            password_data.new_password,
        )
        record_audit_event(
            "auth.password_changed", user_id=current_user.id, username=current_user.username
        )  # noqa: E501
        return {"message": "Password changed successfully"}
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> list[User]:
    """List all users (admin only).

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        _: Current admin user
        db: Database session

    Returns:
        List of users
    """
    # Admin-only user directory for operational management screens.
    return AuthService.list_users(db, skip=skip, limit=limit)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> User:
    """Get user by ID (admin only).

    Args:
        user_id: User ID
        _: Current admin user
        db: Database session

    Returns:
        User information

    Raises:
        HTTPException: If user not found
    """
    user = AuthService.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> User:
    """Update user (admin only).

    Args:
        user_id: User ID
        user_data: User update data
        _: Current admin user
        db: Database session

    Returns:
        Updated user

    Raises:
        HTTPException: If user not found or update fails
    """
    user = AuthService.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    try:
        # Admin updates are separated from self-updates to enforce stronger privilege rules.
        user = AuthService.admin_update_user(db, current_user, user, user_data)
        record_audit_event(
            "auth.user_updated",
            actor_user_id=current_user.id,
            actor_username=current_user.username,
            target_user_id=user.id,
            target_username=user.username,
        )
        return user
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Delete user (admin only).

    Args:
        user_id: User ID
        _: Current admin user
        db: Database session

    Raises:
        HTTPException: If user not found
    """
    user = AuthService.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    try:
        # Admin deletion route applies service-level safeguards before hard delete.
        AuthService.admin_delete_user(db, current_user, user)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err

    record_audit_event(
        "auth.user_deleted",
        actor_user_id=current_user.id,
        actor_username=current_user.username,
        target_user_id=user_id,
        target_username=user.username,
    )
    return {"message": "User deleted successfully"}
