"""Tests for the persistent reference-track and assignment workflow."""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.evaluation import Evaluation, EvaluationStatus, Performance
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
        mfa_enabled=True,
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

    assert analyze_response.status_code == 202
    evaluation_id = analyze_response.json()["evaluation_id"]

    # The background task runs synchronously within TestClient's request/response cycle.
    evaluation_response = client.get(
        f"/api/v1/evaluations/{evaluation_id}",
        headers=_auth_headers(admin_user),
    )
    assert evaluation_response.status_code == 200
    assert evaluation_response.json()["status"] == "completed"
    assert evaluation_response.json()["score"] > 0.0

    db = SessionLocal()
    try:
        performance = db.query(Performance).filter(Performance.id == performance_id).first()
        assert performance is not None
        assert performance.assignment_id == assignment_id
    finally:
        db.close()


def test_musician_cannot_analyze_performance(
    tmp_path: Path,
    admin_user: User,
    musician_user: User,
) -> None:
    """Non-admins cannot upload reference audio for similarity analysis."""
    reference_path = tmp_path / "reference.wav"
    _write_wav(reference_path, 440.0)

    with reference_path.open("rb") as reference_file:
        reference_response = client.post(
            "/api/v1/reference-tracks",
            data={"title": "Reference", "description": "Reference for testing"},
            files={"audio_file": ("reference.wav", reference_file, "audio/wav")},
            headers=_auth_headers(admin_user),
        )

    assignment_response = client.post(
        "/api/v1/assignments",
        data={
            "title": "Reference assignment",
            "description": "Assignment backed by a reference track",
            "reference_track_id": reference_response.json()["id"],
        },
        headers=_auth_headers(admin_user),
    )
    _ = assignment_response.json()["id"]  # assignment registered; performance uses it via track

    performance_path = tmp_path / "performance.wav"
    _write_wav(performance_path, 440.0)

    with performance_path.open("rb") as performance_file:
        performance_response = client.post(
            "/api/v1/performances/upload-audio",
            data={"title": "My performance", "description": "Performance to score"},
            files={"audio_file": ("performance.wav", performance_file, "audio/wav")},
            headers=_auth_headers(musician_user),
        )

    performance_id = performance_response.json()["id"]

    with reference_path.open("rb") as blocked_reference_file:
        analyze_response = client.post(
            f"/api/v1/performances/{performance_id}/analyze-audio",
            files={"reference_audio": ("reference.wav", blocked_reference_file, "audio/wav")},
            headers=_auth_headers(musician_user),
        )

    assert analyze_response.status_code == 403
    assert "only admins can analyze performances" in analyze_response.json()["detail"].lower()


def test_musician_can_delete_uploaded_performance_and_related_evaluation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    admin_user: User,
    musician_user: User,
) -> None:
    """Deleting a performance should remove the record, its evaluation, and the audio file."""
    monkeypatch.setattr(settings, "use_local_upload_storage", True)
    monkeypatch.setattr(settings, "local_upload_dir", str(tmp_path))

    reference_path = tmp_path / "delete-reference.wav"
    _write_wav(reference_path, 440.0)

    with reference_path.open("rb") as reference_file:
        reference_response = client.post(
            "/api/v1/reference-tracks",
            data={"title": "Delete reference", "description": "Delete flow reference"},
            files={"audio_file": ("delete-reference.wav", reference_file, "audio/wav")},
            headers=_auth_headers(admin_user),
        )

    assignment_response = client.post(
        "/api/v1/assignments",
        data={
            "title": "Delete assignment",
            "description": "Assignment for delete flow",
            "reference_track_id": reference_response.json()["id"],
        },
        headers=_auth_headers(admin_user),
    )
    assignment_id = assignment_response.json()["id"]

    performance_path = tmp_path / "delete-performance.wav"
    _write_wav(performance_path, 440.0)

    with performance_path.open("rb") as performance_file:
        submission_response = client.post(
            f"/api/v1/assignments/{assignment_id}/submissions",
            data={"title": "Delete me", "description": "Submission to delete"},
            files={"audio_file": ("delete-performance.wav", performance_file, "audio/wav")},
            headers=_auth_headers(musician_user),
        )

    assert submission_response.status_code == 201
    submission_payload = submission_response.json()
    performance_id = submission_payload["performance"]["id"]
    evaluation_id = submission_payload["evaluation"]["id"]
    stored_path = tmp_path / Path(submission_payload["performance"]["audio_file_url"]).name
    assert stored_path.exists()

    delete_response = client.delete(
        f"/api/v1/performances/{performance_id}",
        headers=_auth_headers(musician_user),
    )

    assert delete_response.status_code == 200
    assert not stored_path.exists()

    db = SessionLocal()
    try:
        assert db.query(Performance).filter(Performance.id == performance_id).first() is None
        assert db.query(Evaluation).filter(Evaluation.id == evaluation_id).first() is None
    finally:
        db.close()


def test_assignment_delete_unlinks_performances_and_reference_track_can_then_be_deleted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    admin_user: User,
    musician_user: User,
) -> None:
    """Deleting an assignment should preserve submissions so the reference track can be removed safely."""  # noqa: E501
    monkeypatch.setattr(settings, "use_local_upload_storage", True)
    monkeypatch.setattr(settings, "local_upload_dir", str(tmp_path))

    reference_path = tmp_path / "cleanup-reference.wav"
    _write_wav(reference_path, 440.0)

    with reference_path.open("rb") as reference_file:
        reference_response = client.post(
            "/api/v1/reference-tracks",
            data={"title": "Cleanup reference", "description": "Reference for cleanup"},
            files={"audio_file": ("cleanup-reference.wav", reference_file, "audio/wav")},
            headers=_auth_headers(admin_user),
        )

    reference_payload = reference_response.json()
    assignment_response = client.post(
        "/api/v1/assignments",
        data={
            "title": "Cleanup assignment",
            "description": "Assignment to remove later",
            "reference_track_id": reference_payload["id"],
        },
        headers=_auth_headers(admin_user),
    )
    assignment_id = assignment_response.json()["id"]

    performance_path = tmp_path / "cleanup-performance.wav"
    _write_wav(performance_path, 440.0)

    with performance_path.open("rb") as performance_file:
        submission_response = client.post(
            f"/api/v1/assignments/{assignment_id}/submissions",
            data={"title": "Keep me", "description": "Submission to preserve"},
            files={"audio_file": ("cleanup-performance.wav", performance_file, "audio/wav")},
            headers=_auth_headers(musician_user),
        )

    performance_id = submission_response.json()["performance"]["id"]
    evaluation_id = submission_response.json()["evaluation"]["id"]
    reference_file_path = tmp_path / Path(reference_payload["audio_file_url"]).name
    assert reference_file_path.exists()

    delete_assignment_response = client.delete(
        f"/api/v1/assignments/{assignment_id}",
        headers=_auth_headers(admin_user),
    )
    assert delete_assignment_response.status_code == 200

    db = SessionLocal()
    try:
        preserved_performance = (
            db.query(Performance).filter(Performance.id == performance_id).first()
        )
        preserved_evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        assert preserved_performance is not None
        assert preserved_performance.assignment_id is None
        assert preserved_evaluation is not None
    finally:
        db.close()

    delete_reference_response = client.delete(
        f"/api/v1/reference-tracks/{reference_payload['id']}",
        headers=_auth_headers(admin_user),
    )
    assert delete_reference_response.status_code == 200
    assert not reference_file_path.exists()


def test_reference_track_delete_requires_assignments_to_be_removed_first(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    admin_user: User,
) -> None:
    """Reference tracks with dependent assignments should not be deleted directly."""
    monkeypatch.setattr(settings, "use_local_upload_storage", True)
    monkeypatch.setattr(settings, "local_upload_dir", str(tmp_path))

    reference_path = tmp_path / "blocked-reference.wav"
    _write_wav(reference_path, 440.0)

    with reference_path.open("rb") as reference_file:
        reference_response = client.post(
            "/api/v1/reference-tracks",
            data={"title": "Blocked reference", "description": "Still in use"},
            files={"audio_file": ("blocked-reference.wav", reference_file, "audio/wav")},
            headers=_auth_headers(admin_user),
        )

    reference_id = reference_response.json()["id"]
    assignment_response = client.post(
        "/api/v1/assignments",
        data={
            "title": "Blocking assignment",
            "description": "Prevents delete",
            "reference_track_id": reference_id,
        },
        headers=_auth_headers(admin_user),
    )
    assert assignment_response.status_code == 201

    delete_response = client.delete(
        f"/api/v1/reference-tracks/{reference_id}",
        headers=_auth_headers(admin_user),
    )
    assert delete_response.status_code == 409
    assert "delete those assignments first" in delete_response.json()["detail"].lower()


def test_admin_can_delete_user_and_clean_up_owned_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    admin_user: User,
    musician_user: User,
) -> None:
    """Deleting a user should remove owned uploads, evaluations, and account data."""
    monkeypatch.setattr(settings, "use_local_upload_storage", True)
    monkeypatch.setattr(settings, "local_upload_dir", str(tmp_path))

    performance_path = tmp_path / "delete-user-performance.wav"
    _write_wav(performance_path, 440.0)

    with performance_path.open("rb") as performance_file:
        upload_response = client.post(
            "/api/v1/performances/upload-audio",
            data={"title": "Owned upload", "description": "Owned by musician to delete"},
            files={"audio_file": ("delete-user-performance.wav", performance_file, "audio/wav")},
            headers=_auth_headers(musician_user),
        )

    assert upload_response.status_code == 201
    performance_payload = upload_response.json()
    performance_id = performance_payload["id"]
    stored_path = tmp_path / Path(performance_payload["audio_file_url"]).name
    assert stored_path.exists()

    evaluation_response = client.post(
        "/api/v1/evaluations",
        json={
            "performance_id": performance_id,
            "score": 81.2,
            "comments": "Cleanup me",
        },
        headers=_auth_headers(admin_user),
    )
    assert evaluation_response.status_code == 201
    evaluation_id = evaluation_response.json()["id"]

    delete_user_response = client.delete(
        f"/api/v1/auth/users/{musician_user.id}",
        headers=_auth_headers(admin_user),
    )
    assert delete_user_response.status_code == 200

    db = SessionLocal()
    try:
        assert db.query(User).filter(User.id == musician_user.id).first() is None
        assert db.query(Performance).filter(Performance.id == performance_id).first() is None
        assert db.query(Evaluation).filter(Evaluation.id == evaluation_id).first() is None
    finally:
        db.close()

    assert not stored_path.exists()


def test_admin_can_change_user_role(
    admin_user: User,
    musician_user: User,
) -> None:
    """Admins can change another user's role."""
    response = client.put(
        f"/api/v1/auth/users/{musician_user.id}",
        json={"role": "admin"},
        headers=_auth_headers(admin_user),
    )

    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_admin_cannot_delete_own_account(admin_user: User) -> None:
    """Admins cannot delete their own account."""
    response = client.delete(
        f"/api/v1/auth/users/{admin_user.id}",
        headers=_auth_headers(admin_user),
    )

    assert response.status_code == 400
    assert "cannot delete your own account" in response.json()["detail"].lower()


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

    list_response = client.get(
        "/api/v1/assignments?limit=500", headers=_auth_headers(musician_user)
    )  # noqa: E501
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
    # Scoring now runs as a background task, so the immediate response has no analysis yet.
    assert submission_payload["analysis"] is None
    assert submission_payload["evaluation"]["status"] == EvaluationStatus.PENDING.value

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
        # TestClient runs FastAPI background tasks synchronously before the
        # request returns, so the score should already be persisted here.
        assert evaluation.status == EvaluationStatus.COMPLETED
        assert evaluation.score is not None
        assert evaluation.score > 0.0
    finally:
        db.close()


def test_musician_submission_survives_missing_reference_audio(
    tmp_path: Path,
    admin_user: User,
    musician_user: User,
) -> None:
    """Missing reference audio should not prevent a musician submission from being created."""
    reference_path = tmp_path / "missing-reference.wav"
    _write_wav(reference_path, 440.0)

    with reference_path.open("rb") as reference_file:
        reference_response = client.post(
            "/api/v1/reference-tracks",
            data={"title": "Missing reference", "description": "Reference for fallback"},
            files={"audio_file": ("missing-reference.wav", reference_file, "audio/wav")},
            headers=_auth_headers(admin_user),
        )

    assert reference_response.status_code == 201
    reference_payload = reference_response.json()

    missing_reference_path = (
        Path.cwd() / settings.local_upload_dir / Path(reference_payload["audio_file_url"]).name
    )  # noqa: E501
    missing_reference_path.unlink(missing_ok=True)

    assignment_response = client.post(
        "/api/v1/assignments",
        data={
            "title": "Week 3 assignment",
            "description": "Submit even if reference is gone",
            "reference_track_id": reference_payload["id"],
        },
        headers=_auth_headers(admin_user),
    )

    assert assignment_response.status_code == 201
    assignment_id = assignment_response.json()["id"]

    performance_path = tmp_path / "fallback-submission.wav"
    _write_wav(performance_path, 440.0)

    with performance_path.open("rb") as performance_file:
        submission_response = client.post(
            f"/api/v1/assignments/{assignment_id}/submissions",
            data={
                "title": "My fallback submission",
                "description": "Recorded at home",
            },
            files={"audio_file": ("fallback-submission.wav", performance_file, "audio/wav")},
            headers=_auth_headers(musician_user),
        )

    assert submission_response.status_code == 201
    submission_payload = submission_response.json()
    assert submission_payload["analysis"] is None
    assert "background" in submission_payload["message"].lower()
    assert submission_payload["evaluation"]["status"] == EvaluationStatus.PENDING.value

    db = SessionLocal()
    try:
        evaluation = (
            db.query(Evaluation)
            .filter(Evaluation.id == submission_payload["evaluation"]["id"])
            .first()
        )
        assert evaluation is not None
        assert evaluation.score is None
        assert evaluation.status == EvaluationStatus.PENDING
    finally:
        db.close()


def test_admin_cannot_submit_performance(
    tmp_path: Path,
    admin_user: User,
    musician_user: User,
) -> None:
    """Admins must not be able to submit a performance via the upload-audio or submissions routes."""  # noqa: E501
    # Reference track and assignment created by admin
    reference_path = tmp_path / "admin-blocked-reference.wav"
    _write_wav(reference_path, 440.0)

    with reference_path.open("rb") as reference_file:
        reference_response = client.post(
            "/api/v1/reference-tracks",
            data={"title": "Admin blocked reference", "description": "Block test"},
            files={"audio_file": ("admin-blocked-reference.wav", reference_file, "audio/wav")},
            headers=_auth_headers(admin_user),
        )
    assert reference_response.status_code == 201

    assignment_response = client.post(
        "/api/v1/assignments",
        data={
            "title": "Admin block assignment",
            "description": "Admin cannot submit against this",
            "reference_track_id": reference_response.json()["id"],
        },
        headers=_auth_headers(admin_user),
    )
    assert assignment_response.status_code == 201
    assignment_id = assignment_response.json()["id"]

    performance_path = tmp_path / "admin-perf.wav"
    _write_wav(performance_path, 440.0)

    # Admin must be rejected from POST /performances/upload-audio
    with performance_path.open("rb") as performance_file:
        upload_response = client.post(
            "/api/v1/performances/upload-audio",
            data={"title": "Admin upload attempt", "description": "Should be blocked"},
            files={"audio_file": ("admin-perf.wav", performance_file, "audio/wav")},
            headers=_auth_headers(admin_user),
        )
    assert upload_response.status_code == 403
    assert "musician" in upload_response.json()["detail"].lower()

    # Admin must be rejected from POST /assignments/{id}/submissions
    with performance_path.open("rb") as performance_file:
        submission_response = client.post(
            f"/api/v1/assignments/{assignment_id}/submissions",
            data={"title": "Admin submission attempt", "description": "Should be blocked"},
            files={"audio_file": ("admin-perf.wav", performance_file, "audio/wav")},
            headers=_auth_headers(admin_user),
        )
    assert submission_response.status_code == 403
    assert "musician" in submission_response.json()["detail"].lower()


def _create_reference_track(tmp_path: Path, admin_user: User, name: str) -> int:
    reference_path = tmp_path / f"{name}.wav"
    _write_wav(reference_path, 440.0)
    with reference_path.open("rb") as reference_file:
        response = client.post(
            "/api/v1/reference-tracks",
            data={"title": name, "description": "Targeting test reference"},
            files={"audio_file": (f"{name}.wav", reference_file, "audio/wav")},
            headers=_auth_headers(admin_user),
        )
    assert response.status_code == 201
    return response.json()["id"]


def test_assignment_targeted_to_specific_musician_is_hidden_from_others(
    tmp_path: Path,
    admin_user: User,
    musician_user: User,
    setup_roles,
) -> None:
    """An assignment targeted at one musician should not be visible/submittable by another."""
    db = setup_roles
    role = db.query(Role).filter(Role.name == RoleEnum.MUSICIAN).first()
    other_username = f"musician-{uuid4().hex[:8]}"
    other_musician = User(
        username=other_username,
        email=f"{other_username}@example.com",
        hashed_password=hash_password("secret123"),
        first_name="Other",
        last_name="Musician",
        role_id=role.id,
        is_active=True,
    )
    db.add(other_musician)
    db.commit()
    db.refresh(other_musician)

    reference_track_id = _create_reference_track(tmp_path, admin_user, "targeted-reference")

    assignment_response = client.post(
        "/api/v1/assignments",
        data={
            "title": "Targeted task",
            "reference_track_id": reference_track_id,
            "target_musician_id": musician_user.id,
        },
        headers=_auth_headers(admin_user),
    )
    assert assignment_response.status_code == 201
    assignment_id = assignment_response.json()["id"]
    assert assignment_response.json()["target_musician_id"] == musician_user.id

    # Targeted musician can see and fetch it.
    targeted_list = client.get("/api/v1/assignments", headers=_auth_headers(musician_user))
    assert any(a["id"] == assignment_id for a in targeted_list.json())
    assert (
        client.get(
            f"/api/v1/assignments/{assignment_id}", headers=_auth_headers(musician_user)
        ).status_code
        == 200
    )

    # Other musician cannot see or fetch it.
    other_list = client.get("/api/v1/assignments", headers=_auth_headers(other_musician))
    assert all(a["id"] != assignment_id for a in other_list.json())
    assert (
        client.get(
            f"/api/v1/assignments/{assignment_id}", headers=_auth_headers(other_musician)
        ).status_code
        == 404
    )

    # Other musician cannot submit a performance against it.
    performance_path = tmp_path / "other-perf.wav"
    _write_wav(performance_path, 440.0)
    with performance_path.open("rb") as performance_file:
        submission_response = client.post(
            f"/api/v1/assignments/{assignment_id}/submissions",
            data={"title": "Sneaky submission"},
            files={"audio_file": ("other-perf.wav", performance_file, "audio/wav")},
            headers=_auth_headers(other_musician),
        )
    assert submission_response.status_code == 404


def test_assignment_targeted_to_instrument_filters_by_instrument_type(
    tmp_path: Path,
    admin_user: User,
    setup_roles,
) -> None:
    """An assignment targeted at an instrument type is only visible to matching musicians."""
    db = setup_roles
    role = db.query(Role).filter(Role.name == RoleEnum.MUSICIAN).first()

    def _make_musician(instrument: str | None) -> User:
        username = f"musician-{uuid4().hex[:8]}"
        user = User(
            username=username,
            email=f"{username}@example.com",
            hashed_password=hash_password("secret123"),
            first_name="Musician",
            last_name="User",
            role_id=role.id,
            is_active=True,
            instrument_type=instrument,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    pianist = _make_musician("Piano")
    guitarist = _make_musician("Guitar")

    reference_track_id = _create_reference_track(tmp_path, admin_user, "piano-reference")

    assignment_response = client.post(
        "/api/v1/assignments",
        data={
            "title": "Piano-only task",
            "reference_track_id": reference_track_id,
            "target_instrument_type": "piano",
        },
        headers=_auth_headers(admin_user),
    )
    assert assignment_response.status_code == 201
    assignment_id = assignment_response.json()["id"]

    pianist_list = client.get("/api/v1/assignments", headers=_auth_headers(pianist))
    assert any(a["id"] == assignment_id for a in pianist_list.json())

    guitarist_list = client.get("/api/v1/assignments", headers=_auth_headers(guitarist))
    assert all(a["id"] != assignment_id for a in guitarist_list.json())
    assert (
        client.get(
            f"/api/v1/assignments/{assignment_id}", headers=_auth_headers(guitarist)
        ).status_code
        == 404
    )


def test_untargeted_assignment_is_visible_to_all_musicians(
    tmp_path: Path,
    admin_user: User,
    musician_user: User,
) -> None:
    """Assignments without targeting fields remain open to every musician (backward compatible)."""
    reference_track_id = _create_reference_track(tmp_path, admin_user, "open-reference")

    assignment_response = client.post(
        "/api/v1/assignments",
        data={"title": "Open task", "reference_track_id": reference_track_id},
        headers=_auth_headers(admin_user),
    )
    assert assignment_response.status_code == 201
    assignment_id = assignment_response.json()["id"]
    assert assignment_response.json()["target_musician_id"] is None
    assert assignment_response.json()["target_instrument_type"] is None

    musician_list = client.get("/api/v1/assignments", headers=_auth_headers(musician_user))
    assert any(a["id"] == assignment_id for a in musician_list.json())


def test_update_assignment_can_set_and_clear_targeting(
    tmp_path: Path,
    admin_user: User,
    musician_user: User,
) -> None:
    """Admins can add targeting to an existing assignment and later clear it."""
    reference_track_id = _create_reference_track(tmp_path, admin_user, "update-reference")

    assignment_response = client.post(
        "/api/v1/assignments",
        data={"title": "Task to retarget", "reference_track_id": reference_track_id},
        headers=_auth_headers(admin_user),
    )
    assignment_id = assignment_response.json()["id"]

    update_response = client.put(
        f"/api/v1/assignments/{assignment_id}",
        data={"target_musician_id": musician_user.id},
        headers=_auth_headers(admin_user),
    )
    assert update_response.status_code == 200
    assert update_response.json()["target_musician_id"] == musician_user.id

    # Clearing targeting: 0 means "no specific musician".
    clear_response = client.put(
        f"/api/v1/assignments/{assignment_id}",
        data={"target_musician_id": 0},
        headers=_auth_headers(admin_user),
    )
    assert clear_response.status_code == 200
    assert clear_response.json()["target_musician_id"] is None


def test_create_assignment_rejects_invalid_target_musician(
    tmp_path: Path, admin_user: User
) -> None:
    """target_musician_id must reference an existing musician (not e.g. an admin)."""
    reference_track_id = _create_reference_track(tmp_path, admin_user, "invalid-target-reference")

    response = client.post(
        "/api/v1/assignments",
        data={
            "title": "Invalid target task",
            "reference_track_id": reference_track_id,
            "target_musician_id": admin_user.id,
        },
        headers=_auth_headers(admin_user),
    )
    assert response.status_code == 400
