"""User management API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.models.user import User
from app.schemas.auth import UserResponse, UserUpdate
from app.services.auth import AuthService

# NOTE: this duplicates the admin user-management endpoints already under
# /auth/users in auth.py (both routers are registered). Frontend currently
# calls the /auth/users versions; kept here for backward compatibility.
router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> list[User]:
    """Get all users (admin only).

    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        List of users
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> User:
    """Get user by ID (admin only).

    Args:
        user_id: User ID
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        User data

    Raises:
        HTTPException: If user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> User:
    """Update user (admin only).

    Args:
        user_id: User ID
        user_update: User update data
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Updated user

    Raises:
        HTTPException: If user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    try:
        return AuthService.admin_update_user(db, current_user, user, user_update)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> dict[str, str]:
    """Delete user (admin only).

    Args:
        user_id: User ID
        db: Database session
        current_user: Current authenticated admin user

    Returns:
        Success message

    Raises:
        HTTPException: If user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    try:
        AuthService.admin_delete_user(db, current_user, user)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err
    return {"message": "User deleted successfully"}
