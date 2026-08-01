"""Authentication and user schemas for request/response validation."""

from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_serializer,
    field_validator,
)

from app.models.user import RoleEnum


class UserBase(BaseModel):
    """Base user schema."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(..., min_length=8)
    role: RoleEnum


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    email: EmailStr | None = None
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    is_active: bool | None = None
    role: RoleEnum | None = None


class UserResponse(UserBase):
    """Schema for user response."""

    id: int
    role: str
    is_active: bool
    email_verified: bool = False
    mfa_enabled: bool = False
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("role", mode="before")
    @classmethod
    def validate_role(cls, value):
        if value is None:
            return None
        if hasattr(value, "name"):
            name = value.name
            if isinstance(name, RoleEnum):
                return name.value
            return str(name)
        return str(value)

    @field_serializer("role")
    def serialize_role(self, role):
        if isinstance(role, str):
            return role
        if hasattr(role, "name"):
            name = role.name
            return name.value if isinstance(name, RoleEnum) else str(name)
        return str(role)


class TokenData(BaseModel):
    """JWT token payload schema."""

    sub: int  # user_id
    username: str
    role: str
    exp: datetime | None = None


class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""

    refresh_token: str = Field(..., description="Refresh token")


class RefreshTokenResponse(BaseModel):
    """Schema for refresh token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    """Schema for login request."""

    username: str
    password: str
    totp_code: str | None = None


class PasswordChangeRequest(BaseModel):
    """Schema for password change request."""

    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)


class PasswordResetRequest(BaseModel):
    """Schema for requesting a password reset email."""

    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    """Schema for completing a password reset."""

    token: str = Field(..., min_length=10)
    new_password: str = Field(..., min_length=8)


class MFASetupResponse(BaseModel):
    """Schema for MFA setup data."""

    secret: str
    otpauth_url: str


class MFAVerifyRequest(BaseModel):
    """Schema for MFA verification."""

    code: str = Field(..., min_length=6, max_length=8)
