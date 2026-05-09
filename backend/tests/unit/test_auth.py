"""Tests for authentication and RBAC."""

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.main import app
from app.models.user import Permission, PermissionEnum, Role, RoleEnum, User

client = TestClient(app)


@pytest.fixture
def db_session():
    """Create a test database session."""
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def setup_test_roles(db_session):
    """Set up test roles."""
    # Create roles
    for role_enum in RoleEnum:
        existing = db_session.query(Role).filter(Role.name == role_enum).first()
        if not existing:
            role = Role(name=role_enum, description=f"{role_enum.value} role")
            db_session.add(role)
    db_session.commit()

    # Create permissions and assign to admin role
    admin_role = db_session.query(Role).filter(Role.name == RoleEnum.ADMIN).first()
    for perm_enum in PermissionEnum:
        existing = db_session.query(Permission).filter(Permission.name == perm_enum).first()
        if not existing:
            perm = Permission(name=perm_enum, description=f"{perm_enum.value} permission")
            db_session.add(perm)
            db_session.flush()
            if admin_role and perm not in admin_role.permissions:
                admin_role.permissions.append(perm)

    db_session.commit()
    return db_session


@pytest.fixture
def test_admin_user(setup_test_roles):
    """Create a test admin user."""
    db = setup_test_roles

    # Check if user already exists
    existing = db.query(User).filter(User.username == "testadmin").first()
    if existing:
        return existing

    role = db.query(Role).filter(Role.name == RoleEnum.ADMIN).first()

    user = User(
        username="testadmin",
        email="testadmin@example.com",
        hashed_password=hash_password("testpassword123"),
        first_name="Test",
        last_name="Admin",
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_musician_user(setup_test_roles):
    """Create a test musician user."""
    db = setup_test_roles

    existing = db.query(User).filter(User.username == "testmusician").first()
    if existing:
        return existing

    role = db.query(Role).filter(Role.name == RoleEnum.MUSICIAN).first()

    user = User(
        username="testmusician",
        email="testmusician@example.com",
        hashed_password=hash_password("testpassword123"),
        first_name="Test",
        last_name="Musician",
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class TestAuthentication:
    """Test authentication endpoints."""

    def test_register_user(self, setup_test_roles, db_session):
        """Test user registration."""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123",
            "first_name": "New",
            "last_name": "User",
            "role": "musician",
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 201
        assert response.json()["username"] == "newuser"
        assert response.json()["email"] == "newuser@example.com"
        assert response.json()["role"] == "musician"

    def test_register_duplicate_user(self, test_musician_user):
        """Test registering with duplicate username."""
        user_data = {
            "username": "testmusician",
            "email": "different@example.com",
            "password": "securepassword123",
            "role": "musician",
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_login_success(self, test_musician_user):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testmusician",
                "password": "testpassword123",
            },
        )

        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
        assert response.json()["expires_in"] > 0

    def test_login_invalid_password(self, test_musician_user):
        """Test login with invalid password."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testmusician",
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]

    def test_login_nonexistent_user(self):
        """Test login with nonexistent user."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "somepassword",
            },
        )

        assert response.status_code == 401


class TestPasswordSecurity:
    """Test password hashing and verification."""

    def test_password_hashing(self):
        """Test password hashing."""
        password = "securepassword123"
        hashed = hash_password(password)

        assert hashed != password
        assert verify_password(password, hashed)

    def test_password_verification_failure(self):
        """Test password verification with wrong password."""
        password = "securepassword123"
        hashed = hash_password(password)

        assert not verify_password("wrongpassword", hashed)


class TestRoleBasedAccess:
    """Test role-based access control."""

    def test_admin_access(self, test_admin_user):
        """Test admin user accessing admin endpoint."""
        # Create token for admin user
        token, _ = create_access_token(
            {
                "sub": test_admin_user.id,
                "username": test_admin_user.username,
                "role": "admin",
            }
        )

        # Try to access admin endpoint
        response = client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_musician_denied_admin_access(self, test_musician_user):
        """Test musician user denied access to admin endpoint."""
        token, _ = create_access_token(
            {
                "sub": test_musician_user.id,
                "username": test_musician_user.username,
                "role": "musician",
            }
        )

        response = client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]

    def test_missing_token(self):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 403

    def test_invalid_token(self):
        """Test accessing protected endpoint with invalid token."""
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.here"}
        )

        assert response.status_code == 403


class TestUserManagement:
    """Test user management endpoints."""

    def test_get_current_user(self, test_musician_user):
        """Test getting current user info."""
        token, _ = create_access_token(
            {
                "sub": test_musician_user.id,
                "username": test_musician_user.username,
                "role": "musician",
            }
        )

        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        assert response.json()["username"] == "testmusician"
        assert response.json()["email"] == "testmusician@example.com"

    def test_update_current_user(self, test_musician_user):
        """Test updating current user."""
        token, _ = create_access_token(
            {
                "sub": test_musician_user.id,
                "username": test_musician_user.username,
                "role": "musician",
            }
        )

        response = client.put(
            "/api/v1/auth/me",
            json={
                "first_name": "Updated",
                "last_name": "Name",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["first_name"] == "Updated"
        assert response.json()["last_name"] == "Name"

    def test_change_password(self, test_musician_user):
        """Test changing password."""
        token, _ = create_access_token(
            {
                "sub": test_musician_user.id,
                "username": test_musician_user.username,
                "role": "musician",
            }
        )

        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "testpassword123",
                "new_password": "newpassword456",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert "successfully" in response.json()["message"]

    def test_change_password_wrong_current(self, test_musician_user):
        """Test changing password with wrong current password."""
        token, _ = create_access_token(
            {
                "sub": test_musician_user.id,
                "username": test_musician_user.username,
                "role": "musician",
            }
        )

        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "wrongpassword",
                "new_password": "newpassword456",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"]

    def test_admin_list_users(self, test_admin_user):
        """Test admin listing all users."""
        token, _ = create_access_token(
            {
                "sub": test_admin_user.id,
                "username": test_admin_user.username,
                "role": "admin",
            }
        )

        response = client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_admin_get_user(self, test_admin_user, test_musician_user):
        """Test admin getting specific user."""
        token, _ = create_access_token(
            {
                "sub": test_admin_user.id,
                "username": test_admin_user.username,
                "role": "admin",
            }
        )

        response = client.get(
            f"/api/v1/auth/users/{test_musician_user.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["username"] == "testmusician"

    def test_admin_update_user(self, test_admin_user, test_musician_user):
        """Test admin updating user."""
        token, _ = create_access_token(
            {
                "sub": test_admin_user.id,
                "username": test_admin_user.username,
                "role": "admin",
            }
        )

        response = client.put(
            f"/api/v1/auth/users/{test_musician_user.id}",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["is_active"] is False


class TestRefreshToken:
    """Test refresh token functionality."""

    def test_login_returns_refresh_token(self, test_musician_user):
        """Test that login returns both access and refresh tokens."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testmusician",
                "password": "testpassword123",
            },
        )

        assert response.status_code == 200
        assert "access_token" in response.json()
        assert "refresh_token" in response.json()
        assert response.json()["token_type"] == "bearer"

    def test_refresh_token_success(self, test_musician_user):
        """Test refreshing access token with valid refresh token."""
        # First login to get tokens
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testmusician",
                "password": "testpassword123",
            },
        )

        refresh_token = login_response.json()["refresh_token"]

        # Refresh the token
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
        assert response.json()["expires_in"] > 0

    def test_refresh_token_invalid(self):
        """Test refresh with invalid refresh token."""
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid.token.here"})

        assert response.status_code == 401
        assert "Invalid or expired refresh token" in response.json()["detail"]

    def test_new_access_token_works(self, test_musician_user):
        """Test that new access token from refresh works for protected endpoint."""
        # First login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testmusician",
                "password": "testpassword123",
            },
        )

        refresh_token = login_response.json()["refresh_token"]

        # Refresh the token
        refresh_response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )

        new_access_token = refresh_response.json()["access_token"]

        # Use new access token to access protected endpoint
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {new_access_token}"}
        )

        assert response.status_code == 200
        assert response.json()["username"] == "testmusician"

    def test_refresh_token_from_inactive_user(self, test_musician_user, db_session):
        """Test that refresh fails for inactive user."""
        # First login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testmusician",
                "password": "testpassword123",
            },
        )

        refresh_token = login_response.json()["refresh_token"]

        # Deactivate user
        test_musician_user.is_active = False
        db_session.commit()

        # Try to refresh
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

        assert response.status_code == 401
        assert "Invalid or expired refresh token" in response.json()["detail"]

    def test_refresh_token_expiration(self, test_musician_user):
        """Test that expired refresh token fails."""
        # Create an already-expired refresh token

        expired_token, _ = create_refresh_token(
            data={
                "sub": test_musician_user.id,
                "username": test_musician_user.username,
                "role": "musician",
            },
            expires_delta=timedelta(seconds=-10),  # Expired 10 seconds ago
        )

        response = client.post("/api/v1/auth/refresh", json={"refresh_token": expired_token})

        assert response.status_code == 401
        assert "Invalid or expired refresh token" in response.json()["detail"]
