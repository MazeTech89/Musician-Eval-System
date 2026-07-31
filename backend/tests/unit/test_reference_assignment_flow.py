"""Tests for the persistent reference-track and assignment workflow."""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.evaluation import Evaluation, Performance
from app.models.user import Role, RoleEnum, User

client = TestClient(app)


def _write_wav(path: Path, frequency: float, duration_seconds: float = 0.15) -> None:
    """Create a simple sine-wave WAV file at the given path."""
    sample_rate = 22050
    total_samples = int(sample_rate * duration_seconds)
    amplitude = 16000

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)

        for sample_index in range(total_samples):
            sample_value = int(
                amplitude * math.sin(2 * math.pi * frequency * sample_index / sample_rate)
            )
            wav_file.writeframes(struct.pack("<h", sample_value))


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
def admin_user(setup_roles):
    """Create a test admin user."""
    db = setup_roles
    role = db.query(Role).filter(Role.name == RoleEnum.ADMIN).first()
    username = f"admin-{uuid4().hex[:8]}"
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password=hash_password("secret123"),
        first_name="Admin",
        last_name="User",
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def musician_user(setup_roles):
    """Create a test musician user."""
    db = setup_roles
    role = db.query(Role).filter(Role.name == RoleEnum.MUSICIAN).first()
    username = f"musician-{uuid4().hex[:8]}"
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password=hash_password("secret123"),
        first_name="Musician",
        last_name="User",
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _auth_headers(user: User) -> dict[str, str]:
    token, _ = create_access_token(
        {"sub": user.id, "username": user.username, "role": user.role.name.value}
    )
    return {"Authorization": f"Bearer {token}"}


def test_create_reference_track_and_assignment(tmp_path: Path, admin_user: User) -> None:
    """Admins can create a reference track and bind it to an assignment."""
    reference_path = tmp_path / "reference.wav"
    _write_wav(reference_path, 440.0)

    with reference_path.open("rb") as reference_file:
        response = client.post(
            "/api/v1/reference-tracks",
            data={"title": "Warm-up", "description": "A reusable warm-up reference"},
            files={"audio_file": ("reference.wav", reference_file, "audio/wav")},
            headers=_auth_headers(admin_user),
        )

    assert response.status_code == 201
    reference_payload = response.json()
    assert reference_payload["title"] == "Warm-up"

    assignment_response = client.post(
        "/api/v1/assignments",
        data={
            "title": "Week 1 assignment",
            "description": "Assignment for the warm-up track",
            "reference_track_id": reference_payload["id"],
        },
        headers=_auth_headers(admin_user),
    )

    assert assignment_response.status_code == 201
    assignment_payload = assignment_response.json()
    assert assignment_payload["reference_track"]["id"] == reference_payload["id"]


def test_analyze_performance_with_assignment(
    tmp_path: Path,
    admin_user: User,
    musician_user: User,
) -> None:
    """Assignments can be used to score performances against a stored reference track."""
    reference_path = tmp_path / "reference.wav"
    _write_wav(reference_path, 440.0)

    with reference_path.open("rb") as reference_file:
        reference_response = client.post(
            "/api/v1/reference-tracks",
            data={"title": "Reference", "description": "Reference for testing"},
            files={"audio_file": ("reference.wav", reference_file, "audio/wav")},
            headers=_auth_headers(admin_user),
        )

    assert reference_response.status_code == 201

    assignment_response = client.post(
        "/api/v1/assignments",
        data={
            "title": "Reference assignment",
            "description": "Assignment backed by a reference track",
            "reference_track_id": reference_response.json()["id"],
        },
        headers=_auth_headers(admin_user),
    )

    assert assignment_response.status_code == 201
    assignment_id = assignment_response.json()["id"]

    performance_path = tmp_path / "performance.wav"
    _write_wav(performance_path, 440.0)

    with performance_path.open("rb") as performance_file:
        performance_response = client.post(
            "/api/v1/performances/upload-audio",
            data={"title": "My performance", "description": "Performance to score"},
            files={"audio_file": ("performance.wav", performance_file, "audio/wav")},
            headers=_auth_headers(musician_user),
        )

    assert performance_response.status_code == 201
    performance_id = performance_response.json()["id"]

    analyze_response = client.post(
        f"/api/v1/assignments/{assignment_id}/performances/{performance_id}/analyze",
        headers=_auth_headers(admin_user),
    )

    assert analyze_response.status_code == 201
    assert analyze_response.json()["score"] > 90.0

    db = SessionLocal()
    try:
        performance = db.query(Performance).filter(Performance.id == performance_id).first()
        assert performance is not None
        assert performance.assignment_id == assignment_id
    finally:
        db.close()


def test_musician_can_submit_assignment_and_receive_score(
    tmp_path: Path,
    admin_user: User,
    musician_user: User,
) -> None:
    """Musicians can upload a recording against an assignment and receive a score."""
    reference_path = tmp_path / "assignment-reference.wav"
    _write_wav(reference_path, 440.0)

    with reference_path.open("rb") as reference_file:
        reference_response = client.post(
            "/api/v1/reference-tracks",
            data={"title": "Assignment reference", "description": "Reference for submission"},
            files={"audio_file": ("assignment-reference.wav", reference_file, "audio/wav")},
            headers=_auth_headers(admin_user),
        )

    assert reference_response.status_code == 201

    assignment_response = client.post(
        "/api/v1/assignments",
        data={
            "title": "Week 2 assignment",
            "description": "Submit against this reference",
            "reference_track_id": reference_response.json()["id"],
        },
        headers=_auth_headers(admin_user),
    )

    assert assignment_response.status_code == 201
    assignment_id = assignment_response.json()["id"]

    list_response = client.get("/api/v1/assignments", headers=_auth_headers(musician_user))
    assert list_response.status_code == 200
    assert any(item["id"] == assignment_id for item in list_response.json())

    performance_path = tmp_path / "submission.wav"
    _write_wav(performance_path, 440.0)

    with performance_path.open("rb") as performance_file:
        submission_response = client.post(
            f"/api/v1/assignments/{assignment_id}/submissions",
            data={
                "title": "My assignment submission",
                "description": "Recorded at home",
            },
            files={"audio_file": ("submission.wav", performance_file, "audio/wav")},
            headers=_auth_headers(musician_user),
        )

    assert submission_response.status_code == 201
    submission_payload = submission_response.json()
    assert submission_payload["analysis"]["score"] > 90.0

    db = SessionLocal()
    try:
        performance = (
            db.query(Performance)
            .filter(Performance.id == submission_payload["performance"]["id"])
            .first()
        )
        evaluation = (
            db.query(Evaluation)
            .filter(Evaluation.id == submission_payload["evaluation"]["id"])
            .first()
        )
        assert performance is not None
        assert performance.assignment_id == assignment_id
        assert evaluation is not None
        assert evaluation.performance_id == performance.id
    finally:
        db.close()
