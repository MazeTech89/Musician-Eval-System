"""Tests for performance audio uploads."""

from datetime import datetime
from io import BytesIO
import math
import struct
import wave

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
    def __init__(self, user_id: int, role: str, username: str = "test-user") -> None:
        self.id = user_id
        self.role = _DummyRole(role)
        self.username = username


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


def _make_wav_bytes() -> bytes:
    buffer = BytesIO()
    sample_rate = 22050
    duration_seconds = 0.05
    total_samples = int(sample_rate * duration_seconds)
    amplitude = 12000

    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for sample_index in range(total_samples):
            sample_value = int(
                amplitude * math.sin(2 * math.pi * 440 * sample_index / sample_rate)
            )
            wav_file.writeframes(struct.pack("<h", sample_value))

    return buffer.getvalue()


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
        files={"audio_file": ("sample.wav", _make_wav_bytes(), "audio/wav")},
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
            self.file = BytesIO(_make_wav_bytes())

    uploaded_path = upload_performance_audio_to_s3(_DummyUploadFile(), 12)

    assert uploaded_path.startswith("/uploads/")
    saved_file = tmp_path / uploaded_path.split("/", 2)[-1]
    assert saved_file.exists()
    assert saved_file.read_bytes() == _make_wav_bytes()


def test_s3_fallback_to_local_storage_when_config_missing(tmp_path, monkeypatch) -> None:
    """Uploads should fall back to local storage when S3 configuration is incomplete."""
    from app.core import config as config_module

    monkeypatch.setattr(config_module.settings, "use_local_upload_storage", False)
    monkeypatch.setattr(config_module.settings, "aws_region", None)
    monkeypatch.setattr(config_module.settings, "aws_access_key_id", None)
    monkeypatch.setattr(config_module.settings, "aws_secret_access_key", None)
    monkeypatch.setattr(config_module.settings, "s3_bucket_name", None)
    monkeypatch.setattr(config_module.settings, "local_upload_dir", str(tmp_path))

    class _DummyUploadFile:
        def __init__(self) -> None:
            self.filename = "demo.wav"
            self.content_type = "audio/wav"
            self.file = BytesIO(_make_wav_bytes())

    uploaded_path = upload_performance_audio_to_s3(_DummyUploadFile(), 12)

    assert uploaded_path.startswith("/uploads/")
    saved_file = tmp_path / uploaded_path.split("/", 2)[-1]
    assert saved_file.exists()
    assert saved_file.read_bytes() == _make_wav_bytes()


def test_upload_audio_rejects_signature_mismatch() -> None:
    """Uploading spoofed audio bytes should fail validation."""

    async def _override_user():
        return _DummyUser(user_id=7, role=RoleEnum.MUSICIAN.value)

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_active_user] = _override_user

    client = TestClient(app)
    response = client.post(
        "/api/v1/performances/upload-audio",
        data={"title": "Spoofed"},
        files={"audio_file": ("fake.wav", b"not-really-wav", "audio/wav")},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "Audio file content does not match its type"
