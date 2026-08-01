"""Authentication and user management services."""

from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from uuid import uuid4

import pyotp
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.audit import record_audit_event, record_security_alert
from app.core.email import send_password_reset_email, send_verification_email
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

        email_verified = True
        email_verification_token = None
        email_verification_token_expires_at = None
        if settings.require_email_verification:
            email_verified = False
            email_verification_token = uuid4().hex
            email_verification_token_expires_at = datetime.now(UTC) + timedelta(hours=24)

        # Create user
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role_id=role.id,
            email_verified=email_verified,
            email_verification_token=email_verification_token,
            email_verification_token_expires_at=email_verification_token_expires_at,
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        record_audit_event(
            "auth.register",
            user_id=user.id,
            username=user.username,
            role=user.role.name.value,
        )

        if settings.require_email_verification and user.email_verification_token:
            verification_url = f"/verify-email?token={user.email_verification_token}"
            try:
                send_verification_email(user.email, verification_url)
            except RuntimeError:
                pass

        return user

    @staticmethod
    def authenticate_user(
        db: Session,
        username: str,
        password: str,
        totp_code: str | None = None,
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
            record_audit_event("auth.login.failed", username=username, reason="inactive_or_missing")
            return None

        if user.lockout_until and user.lockout_until > datetime.now(UTC):
            record_audit_event("auth.login.failed", username=username, reason="locked_out")
            return None

        if not verify_password(password, user.hashed_password):
            user.failed_login_count += 1
            if user.failed_login_count >= 5:
                user.lockout_until = datetime.now(UTC) + timedelta(minutes=15)
                record_security_alert(
                    "auth.account_locked",
                    user_id=user.id,
                    username=user.username,
                    failed_login_count=user.failed_login_count,
                )
            db.commit()
            record_audit_event("auth.login.failed", user_id=user.id, username=user.username, reason="bad_password")
            return None

        if user.mfa_enabled:
            if not totp_code:
                record_audit_event("auth.login.failed", user_id=user.id, username=user.username, reason="missing_mfa")
                return None
            if not user.mfa_secret:
                record_audit_event("auth.login.failed", user_id=user.id, username=user.username, reason="missing_mfa_secret")
                return None
            totp = pyotp.TOTP(user.mfa_secret)
            if not totp.verify(totp_code, valid_window=1):
                user.failed_login_count += 1
                if user.failed_login_count >= 5:
                    user.lockout_until = datetime.now(UTC) + timedelta(minutes=15)
                    record_security_alert(
                        "auth.account_locked",
                        user_id=user.id,
                        username=user.username,
                        failed_login_count=user.failed_login_count,
                    )
                db.commit()
                record_audit_event("auth.login.failed", user_id=user.id, username=user.username, reason="bad_mfa")
                return None

        user.failed_login_count = 0
        user.lockout_until = None

        if settings.require_email_verification and not user.email_verified:
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
        record_audit_event("auth.login.success", user_id=user.id, username=user.username)

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
    def verify_email(db: Session, token: str) -> bool:
        """Verify a user's email using a token."""
        user = db.query(User).filter(User.email_verification_token == token).first()
        if not user:
            return False
        if user.email_verification_token_expires_at and user.email_verification_token_expires_at < datetime.now(UTC):
            return False

        user.email_verified = True
        user.email_verification_token = None
        user.email_verification_token_expires_at = None
        db.commit()
        record_audit_event("auth.email_verified", user_id=user.id, username=user.username)
        return True

    @staticmethod
    def request_password_reset(db: Session, email: str) -> bool:
        """Create a reset token and send the email."""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return False

        token = token_urlsafe(24)
        user.password_reset_token = token
        user.password_reset_token_expires_at = datetime.now(UTC) + timedelta(hours=2)
        db.commit()

        reset_url = f"/reset-password?token={token}"
        try:
            send_password_reset_email(user.email, reset_url)
        except RuntimeError:
            pass
        record_audit_event("auth.password_reset.requested", user_id=user.id, username=user.username)
        return True

    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> bool:
        """Reset a password using a token."""
        user = db.query(User).filter(User.password_reset_token == token).first()
        if not user:
            return False
        if user.password_reset_token_expires_at and user.password_reset_token_expires_at < datetime.now(UTC):
            return False

        user.hashed_password = hash_password(new_password)
        user.password_reset_token = None
        user.password_reset_token_expires_at = None
        user.failed_login_count = 0
        user.lockout_until = None
        db.commit()
        record_audit_event("auth.password_reset.completed", user_id=user.id, username=user.username)
        return True

    @staticmethod
    def setup_mfa(db: Session, user: User) -> tuple[str, str]:
        """Generate MFA secret and provisioning URL for a user."""
        secret = pyotp.random_base32()
        user.mfa_secret = secret
        user.mfa_enabled = False
        db.commit()
        record_audit_event("auth.mfa.setup", user_id=user.id, username=user.username)
        provisioning_uri = pyotp.TOTP(secret).provisioning_uri(name=user.email or user.username, issuer_name="Musician Evaluation")
        return secret, provisioning_uri

    @staticmethod
    def enable_mfa(db: Session, user: User, code: str) -> bool:
        """Enable MFA after a valid verification code."""
        if not user.mfa_secret:
            return False
        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(code, valid_window=1):
            record_audit_event("auth.mfa.enable_failed", user_id=user.id, username=user.username)
            return False
        user.mfa_enabled = True
        db.commit()
        record_audit_event("auth.mfa.enabled", user_id=user.id, username=user.username)
        return True

    @staticmethod
    def disable_mfa(db: Session, user: User, code: str) -> bool:
        """Disable MFA after a valid verification code."""
        if not user.mfa_secret:
            return False
        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(code, valid_window=1):
            record_audit_event("auth.mfa.disable_failed", user_id=user.id, username=user.username)
            return False
        user.mfa_enabled = False
        user.mfa_secret = None
        db.commit()
        record_audit_event("auth.mfa.disabled", user_id=user.id, username=user.username)
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
            record_audit_event("auth.refresh.failed", user_id=token_data.sub)
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
