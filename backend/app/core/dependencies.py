"""FastAPI dependencies for authentication and authorization."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import RoleEnum, User
from app.services.auth import AuthService, RoleService

# HTTP Bearer scheme
security = HTTPBearer(description="JWT Bearer token")


async def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Get the current authenticated user.

    Args:
        credentials: HTTP Bearer credentials
        db: Database session

    Returns:
        Current user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    token_data = decode_token(token)

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = AuthService.get_user_by_id(db, token_data.sub)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get the current active user (alias for get_current_user with stricter checks).

    Args:
        current_user: Current user from get_current_user

    Returns:
        Current user if active

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    return current_user


def require_role(*allowed_roles: RoleEnum):
    """Dependency factory for role-based access control.

    Args:
        allowed_roles: Roles that are allowed to access the resource

    Returns:
        Dependency function
    """

    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        """Check if user has required role.

        Args:
            current_user: Current user

        Returns:
            Current user if authorized

        Raises:
            HTTPException: If user doesn't have required role
        """
        if current_user.role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this action",
            )
        return current_user

    return role_checker


def require_permission(*permissions: str):
    """Dependency factory for permission-based access control.

    Args:
        permissions: Permissions required to access the resource

    Returns:
        Dependency function
    """

    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db),
    ) -> User:
        """Check if user has required permissions.

        Args:
            current_user: Current user
            db: Database session

        Returns:
            Current user if authorized

        Raises:
            HTTPException: If user doesn't have required permissions
        """
        user_permissions = RoleService.get_user_permissions(db, current_user)

        if not any(perm in user_permissions for perm in permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this action",
            )
        return current_user

    return permission_checker


async def get_current_admin(
    current_user: User = Depends(require_role(RoleEnum.ADMIN)),
) -> User:
    """Dependency for admin-only endpoints.

    Args:
        current_user: Current user (already validated as admin)

    Returns:
        Current user
    """
    return current_user


async def get_current_evaluator_or_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Dependency for evaluator and admin endpoints.

    Args:
        current_user: Current user

    Returns:
        Current user if has required role

    Raises:
        HTTPException: If user is not evaluator or admin
    """
    if current_user.role.name not in [RoleEnum.EVALUATOR, RoleEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only evaluators and admins can access this resource",
        )
    return current_user
