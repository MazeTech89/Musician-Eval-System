"""Upload validation helpers for audio files."""

from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.audit import record_security_alert
from app.core.config import settings

ALLOWED_AUDIO_CONTENT_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/x-mp3",
    "audio/x-mpeg",
    "audio/wav",
    "audio/x-wav",
    "audio/ogg",
    "audio/webm",
    "audio/mp4",
    "audio/flac",
}

ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".webm", ".mp4", ".flac"}


def _matches_signature(content_type: str, header: bytes) -> bool:
    if content_type in {"audio/wav", "audio/x-wav"}:
        return len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WAVE"
    if content_type == "audio/ogg":
        return header.startswith(b"OggS")
    if content_type == "audio/flac":
        return header.startswith(b"fLaC")
    if content_type == "audio/webm":
        return header.startswith(b"\x1a\x45\xdf\xa3")
    if content_type == "audio/mp4":
        return len(header) >= 8 and header[4:8] == b"ftyp"
    if content_type in {"audio/mpeg", "audio/mp3", "audio/x-mp3", "audio/x-mpeg"}:
        return header.startswith(b"ID3") or (
            len(header) >= 2 and header[0] == 0xFF and header[1] & 0xE0 == 0xE0
        )
    return False


def validate_audio_upload(audio_file: UploadFile) -> None:
    """Validate an uploaded audio file before persistence."""
    if audio_file.content_type not in ALLOWED_AUDIO_CONTENT_TYPES:
        record_security_alert(
            "upload.rejected",
            reason="unsupported_content_type",
            content_type=audio_file.content_type,
            filename=audio_file.filename,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported audio file type",
        )

    filename = audio_file.filename or ""
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_AUDIO_EXTENSIONS:
        record_security_alert(
            "upload.rejected",
            reason="unsupported_extension",
            content_type=audio_file.content_type,
            filename=audio_file.filename,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported audio file extension",
        )

    audio_file.file.seek(0, 2)
    file_size = audio_file.file.tell()
    audio_file.file.seek(0)
    max_size_bytes = settings.max_audio_upload_size_mb * 1024 * 1024
    if file_size <= 0:
        record_security_alert(
            "upload.rejected",
            reason="empty_file",
            content_type=audio_file.content_type,
            filename=audio_file.filename,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio upload is empty",
        )
    if file_size > max_size_bytes:
        record_security_alert(
            "upload.rejected",
            reason="too_large",
            content_type=audio_file.content_type,
            filename=audio_file.filename,
            size_bytes=file_size,
        )
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Audio upload must be {settings.max_audio_upload_size_mb} MB or smaller",
        )

    header = audio_file.file.read(16)
    audio_file.file.seek(0)
    if not _matches_signature(audio_file.content_type, header):
        record_security_alert(
            "upload.rejected",
            reason="bad_signature",
            content_type=audio_file.content_type,
            filename=audio_file.filename,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio file content does not match its type",
        )
