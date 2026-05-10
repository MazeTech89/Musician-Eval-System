"""Authentication and user schemas for request/response validation."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

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
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None = None

    class Config:
        from_attributes = True


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


class PasswordChangeRequest(BaseModel):
    """Schema for password change request."""

    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)
