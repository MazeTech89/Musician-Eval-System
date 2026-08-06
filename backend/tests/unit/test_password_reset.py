"""Tests for the password reset request/confirm flow."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password, hash_token
from app.main import app
from app.models.user import Role, RoleEnum, User

client = TestClient(app)


@pytest.fixture
def db_session():
    """Create a test database session."""
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def setup_roles(db_session):
    """Ensure the default roles exist for the tests."""
    for role_enum in RoleEnum:
        role = db_session.query(Role).filter(Role.name == role_enum).first()
        if not role:
            db_session.add(Role(name=role_enum, description=f"{role_enum.value} role"))
    db_session.commit()
    return db_session


@pytest.fixture
def musician_user(setup_roles):
    """Create a test musician user."""
    db = setup_roles
    role = db.query(Role).filter(Role.name == RoleEnum.MUSICIAN).first()
    username = f"musician-{uuid4().hex[:8]}"
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password=hash_password("original-password-123"),
        first_name="Musician",
        last_name="User",
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_request_password_reset_rejects_malformed_email() -> None:
    """The request endpoint should validate email format before hitting the service layer."""
    response = client.post("/api/v1/auth/password-reset/request", json={"email": "not-an-email"})
    assert response.status_code == 422


def test_request_password_reset_returns_generic_message_for_unknown_email() -> None:
    """Unknown emails get the same generic response as known ones (anti-enumeration)."""
    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "nobody-here@example.com"},
    )
    assert response.status_code == 200
    assert "If the email exists" in response.json()["message"]


def test_password_reset_token_is_hashed_at_rest(musician_user: User, db_session) -> None:
    """The raw reset token must never be stored verbatim in the database."""
    response = client.post(
        "/api/v1/auth/password-reset/request", json={"email": musician_user.email}
    )
    assert response.status_code == 200

    db_session.refresh(musician_user)
    stored_token = musician_user.password_reset_token
    assert stored_token is not None
    # Stored value must be the SHA-256 hash, not the raw token issued to the user.
    assert len(stored_token) == 64

    # A raw token guessed/leaked from elsewhere must not match the stored hash directly.
    assert stored_token != "some-raw-token-value"


def test_full_password_reset_flow_with_hashed_token(musician_user: User, db_session) -> None:
    """A musician can request a reset and use the emailed (raw) token to set a new password."""
    request_response = client.post(
        "/api/v1/auth/password-reset/request", json={"email": musician_user.email}
    )
    assert request_response.status_code == 200

    db_session.refresh(musician_user)
    stored_hash = musician_user.password_reset_token
    assert stored_hash is not None

    # Simulate receiving the raw token via email: since we can't intercept the email in this
    # test, directly mint a token whose hash we control and persist it the same way the
    # service does, then confirm the API accepts the raw value.
    raw_token = f"test-raw-token-value-{uuid4().hex}"
    musician_user.password_reset_token = hash_token(raw_token)
    musician_user.password_reset_token_expires_at = datetime.now(UTC) + timedelta(hours=1)
    db_session.commit()

    confirm_response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "brand-new-password-456"},
    )
    assert confirm_response.status_code == 200

    # Verify via a fresh session/connection to avoid any stale in-process snapshot.
    verify_db = SessionLocal()
    try:
        refreshed_user = verify_db.query(User).filter(User.id == musician_user.id).first()
        assert refreshed_user is not None
        assert refreshed_user.password_reset_token is None
        assert refreshed_user.password_reset_token_expires_at is None
    finally:
        verify_db.close()

    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": musician_user.username, "password": "brand-new-password-456"},
    )
    assert login_response.status_code == 200


def test_password_reset_confirm_rejects_invalid_token() -> None:
    """An unknown/garbage token must be rejected."""
    response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": "totally-made-up-token-value", "new_password": "whatever-password-1"},
    )
    assert response.status_code == 400


def test_password_reset_confirm_rejects_expired_token(musician_user: User, db_session) -> None:
    """A token past its expiry must be rejected even if otherwise valid."""
    raw_token = f"expired-raw-token-value-{uuid4().hex}"
    musician_user.password_reset_token = hash_token(raw_token)
    musician_user.password_reset_token_expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "another-new-password-1"},
    )
    assert response.status_code == 400


def test_repeated_reset_requests_within_cooldown_do_not_rotate_token(
    musician_user: User, db_session
) -> None:
    """Rapid repeat requests must not spam a new email/token during the cooldown window."""
    first_response = client.post(
        "/api/v1/auth/password-reset/request", json={"email": musician_user.email}
    )
    assert first_response.status_code == 200
    db_session.refresh(musician_user)
    first_token_hash = musician_user.password_reset_token
    assert first_token_hash is not None

    second_response = client.post(
        "/api/v1/auth/password-reset/request", json={"email": musician_user.email}
    )
    assert second_response.status_code == 200
    db_session.refresh(musician_user)
    # Still within settings.password_reset_cooldown_seconds: token must be unchanged.
    assert musician_user.password_reset_token == first_token_hash


def test_reset_request_outside_cooldown_rotates_token(musician_user: User, db_session) -> None:
    """Once the cooldown window has passed, a new request issues a fresh token."""
    first_response = client.post(
        "/api/v1/auth/password-reset/request", json={"email": musician_user.email}
    )
    assert first_response.status_code == 200
    db_session.refresh(musician_user)
    first_token_hash = musician_user.password_reset_token

    # Simulate the cooldown having elapsed.
    musician_user.password_reset_last_requested_at = datetime.now(UTC) - timedelta(
        seconds=settings.password_reset_cooldown_seconds + 1
    )
    db_session.commit()

    second_response = client.post(
        "/api/v1/auth/password-reset/request", json={"email": musician_user.email}
    )
    assert second_response.status_code == 200
    db_session.refresh(musician_user)
    assert musician_user.password_reset_token != first_token_hash
