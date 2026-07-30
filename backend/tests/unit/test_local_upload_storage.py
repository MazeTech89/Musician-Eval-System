"""Tests for local audio upload storage."""

from io import BytesIO

from fastapi import UploadFile

from app.core.config import settings
from app.services.s3_storage import upload_audio_to_s3


def test_upload_audio_uses_local_storage(tmp_path, monkeypatch) -> None:
    """Uploads should be written to local disk when local storage is enabled."""
    monkeypatch.setattr(settings, "use_local_upload_storage", True)
    monkeypatch.setattr(settings, "local_upload_dir", str(tmp_path))

    audio_file = UploadFile(filename="sample.wav", file=BytesIO(b"audio-bytes"))
    upload_path = upload_audio_to_s3(audio_file=audio_file, owner_id=7, collection="performances")

    assert upload_path.startswith("/uploads/performances/7/")

    saved_name = upload_path.rsplit("/", 1)[-1]
    saved_file = tmp_path / "performances" / "7" / saved_name
    assert saved_file.exists()
    assert saved_file.read_bytes() == b"audio-bytes"
