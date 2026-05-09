"""Authentication and user management services."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import Role, RoleEnum, User
from app.schemas.auth import TokenResponse, UserCreate, UserUpdate


class AuthService:
    """Service for authentication operations."""

    @staticmethod
    def register_user(
        db: Session,
        user_data: UserCreate,
    ) -> User:
        """Register a new user.

        Args:
            db: Database session
            user_data: User creation data

        Raises:
            ValueError: If user already exists

        Returns:
            Created user
        """
        # Check if user already exists
        existing_user = (
            db.query(User)
            .filter((User.username == user_data.username) | (User.email == user_data.email))
            .first()
        )

        if existing_user:
            raise ValueError("User with this username or email already exists")

        # Get or create role
        role = db.query(Role).filter(Role.name == user_data.role).first()
        if not role:
            raise ValueError(f"Role {user_data.role} not found")

        # Create user
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role_id=role.id,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def authenticate_user(
        db: Session,
        username: str,
        password: str,
    ) -> TokenResponse | None:
        """Authenticate user and return token.

        Args:
            db: Database session
            username: Username
            password: Password

        Returns:
            TokenResponse if authentication successful, None otherwise
        """
        user = db.query(User).filter(User.username == username).first()

        if not user or not user.is_active:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        # Create access token
        access_token, access_expires = create_access_token(
            data={
                "sub": user.id,
                "username": user.username,
                "role": user.role.name.value,
            }
        )

        # Create refresh token
        refresh_token, _refresh_expires = create_refresh_token(
            data={
                "sub": user.id,
                "username": user.username,
                "role": user.role.name.value,
            }
        )

        # Update last login
        user.last_login = datetime.now(UTC)
        db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int((access_expires - datetime.now(UTC)).total_seconds()),
        )

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User | None:
        """Get user by ID.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User if found, None otherwise
        """
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> User | None:
        """Get user by username.

        Args:
            db: Database session
            username: Username

        Returns:
            User if found, None otherwise
        """
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def update_user(
        db: Session,
        user: User,
        user_data: UserUpdate,
    ) -> User:
        """Update user information.

        Args:
            db: Database session
            user: User to update
            user_data: Update data

        Returns:
            Updated user
        """
        update_data = user_data.dict(exclude_unset=True)

        # Handle role update
        if "role" in update_data:
            role = db.query(Role).filter(Role.name == update_data["role"]).first()
            if not role:
                raise ValueError(f"Role {update_data['role']} not found")
            update_data["role_id"] = role.id
            del update_data["role"]

        for field, value in update_data.items():
            setattr(user, field, value)

        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def change_password(
        db: Session,
        user: User,
        current_password: str,
        new_password: str,
    ) -> bool:
        """Change user password.

        Args:
            db: Database session
            user: User to update
            current_password: Current password
            new_password: New password

        Returns:
            True if successful

        Raises:
            ValueError: If current password is incorrect
        """
        if not verify_password(current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")

        user.hashed_password = hash_password(new_password)
        db.commit()

        return True

    @staticmethod
    def refresh_access_token(
        db: Session,
        refresh_token: str,
    ) -> TokenResponse | None:
        """Refresh an access token using a refresh token.

        Args:
            db: Database session
            refresh_token: Refresh token

        Returns:
            TokenResponse with new access token if successful, None otherwise
        """
        # Decode refresh token
        token_data = decode_refresh_token(refresh_token)

        if not token_data:
            return None

        # Get user
        user = AuthService.get_user_by_id(db, token_data.sub)

        if not user or not user.is_active:
            return None

        # Create new access token
        access_token, access_expires = create_access_token(
            data={
                "sub": user.id,
                "username": user.username,
                "role": user.role.name.value,
            }
        )

        return TokenResponse(
            access_token=access_token,
            expires_in=int((access_expires - datetime.now(UTC)).total_seconds()),
        )

    @staticmethod
    def list_users(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        role: RoleEnum | None = None,
    ) -> list[User]:
        """List users with optional filtering.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            role: Optional role filter

        Returns:
            List of users
        """
        query = db.query(User)

        if role:
            role_obj = db.query(Role).filter(Role.name == role).first()
            if role_obj:
                query = query.filter(User.role_id == role_obj.id)

        return query.offset(skip).limit(limit).all()


class RoleService:
    """Service for role management."""

    @staticmethod
    def get_role_by_name(db: Session, role_name: RoleEnum) -> Role | None:
        """Get role by name.

        Args:
            db: Database session
            role_name: Role name

        Returns:
            Role if found, None otherwise
        """
        return db.query(Role).filter(Role.name == role_name).first()

    @staticmethod
    def get_user_permissions(db: Session, user: User) -> list[str]:
        """Get all permissions for a user.

        Args:
            db: Database session
            user: User object

        Returns:
            List of permission names
        """
        role = user.role
        if not role:
            return []

        return [perm.name.value for perm in role.permissions]
