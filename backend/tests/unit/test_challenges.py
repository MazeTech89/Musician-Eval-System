"""Tests for reference tracks, assignments, and submissions."""

from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.database import SessionLocal, get_db
from app.core.dependencies import get_current_active_user
from app.main import app
from app.models.challenge import Assignment, ReferenceTrack, Submission
from app.models.user import Role, RoleEnum, User
from app.core.security import hash_password

client = TestClient(app)


class _DummyRole:
    def __init__(self, name: str) -> None:
        self.name = name


class _DummyUser:
    def __init__(self, user_id: int, role: str) -> None:
        self.id = user_id
        self.role = _DummyRole(role)


class _DummyDB:
    def add(self, obj) -> None:  # noqa: ANN001
        self._obj = obj

    def commit(self) -> None:
        return None

    def refresh(self, obj) -> None:  # noqa: ANN001
        if getattr(obj, "id", None) is None:
            obj.id = 1000
        if hasattr(obj, "created_at") and getattr(obj, "created_at", None) is None:
            obj.created_at = datetime.utcnow()
        if hasattr(obj, "updated_at") and getattr(obj, "updated_at", None) is None:
            obj.updated_at = datetime.utcnow()


def _override_db():
    yield _DummyDB()


def _override_user(role: str, user_id: int = 1):
    async def _inner():
        return _DummyUser(user_id=user_id, role=role)

    return _inner


def _seed_role(db, role_name: RoleEnum) -> Role:
    role = db.query(Role).filter(Role.name == role_name).first()
    if role:
        return role
    role = Role(name=role_name, description=f"{role_name.value} role")
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def _seed_user(db, username: str, role_name: RoleEnum) -> User:
    role = _seed_role(db, role_name)
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        existing.role_id = role.id
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        return existing

    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password=hash_password("Password123!"),
        first_name=username.capitalize(),
        last_name="User",
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_admin_can_create_reference_track(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.v1.challenges.upload_audio_to_s3",
        lambda audio_file, owner_id, collection: f"s3://bucket/{collection}/{owner_id}/{audio_file.filename}",
    )

    app.dependency_overrides[get_current_active_user] = _override_user("admin", user_id=11)
    app.dependency_overrides[get_db] = _override_db

    response = client.post(
        "/api/v1/challenges/reference-tracks",
        data={"title": "Original song", "description": "Reference track"},
        files={"audio_file": ("original.wav", b"audio-bytes", "audio/wav")},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["title"] == "Original song"
    assert response.json()["audio_file_url"].startswith("s3://bucket/reference-tracks/11/")


def test_musician_cannot_create_reference_track(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.v1.challenges.upload_audio_to_s3",
        lambda audio_file, owner_id, collection: f"s3://bucket/{collection}/{owner_id}/{audio_file.filename}",
    )

    app.dependency_overrides[get_current_active_user] = _override_user("musician", user_id=12)
    app.dependency_overrides[get_db] = _override_db

    response = client.post(
        "/api/v1/challenges/reference-tracks",
        data={"title": "Original song", "description": "Reference track"},
        files={"audio_file": ("original.wav", b"audio-bytes", "audio/wav")},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 403


def test_admin_can_create_assignment() -> None:
    db = SessionLocal()
    try:
        admin_user = _seed_user(db, f"admin-{uuid4().hex[:8]}", RoleEnum.ADMIN)
        reference_track = ReferenceTrack(
            title=f"Ref {uuid4().hex}",
            description="Seeded reference",
            audio_file_url="s3://bucket/reference.wav",
            uploaded_by_id=admin_user.id,
        )
        db.add(reference_track)
        db.commit()
        db.refresh(reference_track)

        app.dependency_overrides[get_current_active_user] = _override_user("admin", user_id=admin_user.id)

        response = client.post(
            "/api/v1/challenges/assignments",
            json={
                "title": "Echo this melody",
                "description": "Replicate the original song",
                "reference_track_id": reference_track.id,
                "target_role": "musician",
                "is_active": True,
            },
        )

        app.dependency_overrides.clear()

        assert response.status_code == 201
        assert response.json()["reference_track"]["id"] == reference_track.id
        assert response.json()["created_by_id"] == admin_user.id
    finally:
        db.close()


def test_musician_can_submit_assignment(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.v1.challenges.upload_audio_to_s3",
        lambda audio_file, owner_id, collection: f"s3://bucket/{collection}/{owner_id}/{audio_file.filename}",
    )

    db = SessionLocal()
    try:
        musician_user = _seed_user(db, f"musician-{uuid4().hex[:8]}", RoleEnum.MUSICIAN)
        admin_user = _seed_user(db, f"admin-{uuid4().hex[:8]}", RoleEnum.ADMIN)
        reference_track = ReferenceTrack(
            title=f"Ref {uuid4().hex}",
            description="Seeded reference",
            audio_file_url="s3://bucket/reference.wav",
            uploaded_by_id=admin_user.id,
        )
        db.add(reference_track)
        db.commit()
        db.refresh(reference_track)

        assignment = Assignment(
            title="Echo this melody",
            description="Replicate the original song",
            reference_track_id=reference_track.id,
            created_by_id=admin_user.id,
            target_role="musician",
            is_active=True,
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        app.dependency_overrides[get_current_active_user] = _override_user("musician", user_id=musician_user.id)

        response = client.post(
            f"/api/v1/challenges/assignments/{assignment.id}/submit",
            data={"notes": "Recorded on guitar"},
            files={"audio_file": ("submission.wav", b"audio-bytes", "audio/wav")},
        )

        app.dependency_overrides.clear()

        assert response.status_code == 201
        assert response.json()["assignment_id"] == assignment.id
        assert response.json()["musician_id"] == musician_user.id
        assert response.json()["status"] == "pending_analysis"
    finally:
        db.close()
