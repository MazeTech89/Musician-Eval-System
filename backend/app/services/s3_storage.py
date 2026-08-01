"""Storage helpers for performance audio files."""

from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import UploadFile

from app.core.config import settings
from app.core.upload_security import validate_audio_upload


class S3StorageError(Exception):
    """Raised when S3 storage operations fail."""


def is_s3_configured() -> bool:
    """Return whether minimum S3 configuration is present."""
    return bool(settings.s3_bucket_name and settings.aws_region)


def _build_local_upload_path(musician_id: int, filename: str) -> Path:
    """Build a deterministic local path for uploaded audio files."""
    upload_dir = Path(settings.local_upload_dir)
    if not upload_dir.is_absolute():
        upload_dir = Path.cwd() / upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(filename).suffix.lower() or ".bin"
    file_name = f"{musician_id}_{uuid4().hex}{suffix}"
    return upload_dir / file_name


def upload_performance_audio_to_local_storage(audio_file: UploadFile, musician_id: int) -> str:
    """Persist uploaded audio to disk and return a local URL."""
    validate_audio_upload(audio_file)
    target_path = _build_local_upload_path(
        musician_id=musician_id,
        filename=audio_file.filename or "upload.bin",
    )

    audio_file.file.seek(0)
    target_path.write_bytes(audio_file.file.read())
    return f"/uploads/{target_path.name}"


def _build_s3_client():
    session_kwargs: dict[str, str] = {}
    if settings.aws_access_key_id:
        session_kwargs["aws_access_key_id"] = settings.aws_access_key_id
    if settings.aws_secret_access_key:
        session_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key

    session = boto3.session.Session(**session_kwargs)
    client_kwargs = {
        "service_name": "s3",
        "region_name": settings.aws_region,
    }
    if settings.s3_endpoint_url:
        client_kwargs["endpoint_url"] = settings.s3_endpoint_url
    return session.client(**client_kwargs)


def _build_object_key(musician_id: int, filename: str) -> str:
    suffix = Path(filename).suffix.lower() or ".bin"
    return f"performances/{musician_id}/{uuid4().hex}{suffix}"


def upload_performance_audio_to_s3(audio_file: UploadFile, musician_id: int) -> str:
    """Upload a performance audio file to the configured storage backend."""
    validate_audio_upload(audio_file)
    if settings.use_local_upload_storage:
        return upload_performance_audio_to_local_storage(audio_file, musician_id)

    if not is_s3_configured():
        return upload_performance_audio_to_local_storage(audio_file, musician_id)

    if not settings.s3_bucket_name:
        raise S3StorageError("S3 bucket is not configured.")

    object_key = _build_object_key(musician_id=musician_id, filename=audio_file.filename or "")
    s3_client = _build_s3_client()
    content_type = audio_file.content_type or "application/octet-stream"

    try:
        audio_file.file.seek(0)
        s3_client.upload_fileobj(
            Fileobj=audio_file.file,
            Bucket=settings.s3_bucket_name,
            Key=object_key,
            ExtraArgs={"ContentType": content_type},
        )
    except (BotoCoreError, ClientError) as err:
        raise S3StorageError("Failed to upload audio file to S3.") from err

    return f"s3://{settings.s3_bucket_name}/{object_key}"


def delete_audio_file(audio_file_url: str | None) -> None:
    """Delete a stored audio file from the configured backend."""
    if not audio_file_url:
        return

    if audio_file_url.startswith("s3://"):
        if not is_s3_configured():
            raise S3StorageError("S3 delete is not configured.")

        object_path = audio_file_url.removeprefix("s3://")
        bucket_name, _, object_key = object_path.partition("/")
        if not bucket_name or not object_key:
            raise S3StorageError("Stored S3 audio reference is invalid.")

        s3_client = _build_s3_client()
        try:
            s3_client.delete_object(Bucket=bucket_name, Key=object_key)
        except (BotoCoreError, ClientError) as err:
            raise S3StorageError("Failed to delete audio file from S3.") from err
        return

    candidate_path, _ = materialize_audio_file(audio_file_url)
    candidate_path.unlink(missing_ok=True)


def materialize_audio_file(audio_file_url: str) -> tuple[Path, bool]:
    """Return a readable local path for a stored audio file.

    The boolean indicates whether the returned path is temporary and should be deleted
    after use.
    """
    if not audio_file_url:
        raise ValueError("Audio file is missing.")

    if audio_file_url.startswith("s3://"):
        if not is_s3_configured():
            raise S3StorageError("S3 download is not configured.")

        object_path = audio_file_url.removeprefix("s3://")
        bucket_name, _, object_key = object_path.partition("/")
        if not bucket_name or not object_key:
            raise S3StorageError("Stored S3 audio reference is invalid.")

        suffix = Path(object_key).suffix.lower() or ".bin"
        temp_file = NamedTemporaryFile(suffix=suffix, delete=False)
        temp_file.close()

        s3_client = _build_s3_client()
        try:
            with Path(temp_file.name).open("wb") as local_file:
                s3_client.download_fileobj(bucket_name, object_key, local_file)
        except (BotoCoreError, ClientError) as err:
            Path(temp_file.name).unlink(missing_ok=True)
            raise S3StorageError("Failed to download audio file from S3.") from err

        return Path(temp_file.name), True

    if audio_file_url.startswith("/uploads/"):
        upload_dir = Path(settings.local_upload_dir)
        if not upload_dir.is_absolute():
            upload_dir = Path.cwd() / upload_dir
        return upload_dir / Path(audio_file_url).name, False

    candidate_path = Path(audio_file_url)
    if not candidate_path.is_absolute():
        candidate_path = Path.cwd() / candidate_path
    return candidate_path, False
