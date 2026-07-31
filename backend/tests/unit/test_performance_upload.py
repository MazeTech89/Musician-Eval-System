"""Tests for performance audio uploads."""

from datetime import datetime
from io import BytesIO

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.main import app
from app.models.user import RoleEnum
from app.services.s3_storage import upload_performance_audio_to_s3


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
        obj.id = 999
        obj.submitted_at = datetime.utcnow()


def _override_db():
    yield _DummyDB()


def test_upload_audio_creates_performance(monkeypatch) -> None:
    """Uploading valid audio should create a performance with S3 URI."""

    async def _override_user():
        return _DummyUser(user_id=7, role=RoleEnum.MUSICIAN.value)

    def _mock_upload(audio_file, musician_id: int) -> str:  # noqa: ANN001
        assert musician_id == 7
        assert audio_file.filename == "sample.wav"
        return "s3://test-bucket/performances/7/sample.wav"

    monkeypatch.setattr(
        "app.api.v1.performances.upload_performance_audio_to_s3",
        _mock_upload,
    )

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_active_user] = _override_user

    client = TestClient(app)
    response = client.post(
        "/api/v1/performances/upload-audio",
        data={"title": "My take", "description": "Practice recording"},
        files={"audio_file": ("sample.wav", b"wav-bytes", "audio/wav")},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My take"
    assert data["description"] == "Practice recording"
    assert data["audio_file_url"] == "s3://test-bucket/performances/7/sample.wav"
    assert data["musician_id"] == 7
    assert data["status"] == "pending"


def test_upload_audio_rejects_invalid_content_type() -> None:
    """Uploading unsupported content type should fail with 400."""

    async def _override_user():
        return _DummyUser(user_id=7, role=RoleEnum.MUSICIAN.value)

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_active_user] = _override_user

    client = TestClient(app)
    response = client.post(
        "/api/v1/performances/upload-audio",
        data={"title": "Bad upload"},
        files={"audio_file": ("script.txt", b"not-audio", "text/plain")},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported audio file type"


def test_local_upload_storage_fallback_writes_to_disk(tmp_path, monkeypatch) -> None:
    """Local storage should persist uploads to disk when enabled."""
    from app.core import config as config_module

    monkeypatch.setattr(config_module.settings, "use_local_upload_storage", True)
    monkeypatch.setattr(config_module.settings, "local_upload_dir", str(tmp_path))

    class _DummyUploadFile:
        def __init__(self) -> None:
            self.filename = "demo.wav"
            self.content_type = "audio/wav"
            self.file = BytesIO(b"wav-bytes")

    uploaded_path = upload_performance_audio_to_s3(_DummyUploadFile(), 12)

    assert uploaded_path.startswith("/uploads/")
    saved_file = tmp_path / uploaded_path.split("/", 2)[-1]
    assert saved_file.exists()
    assert saved_file.read_bytes() == b"wav-bytes"
