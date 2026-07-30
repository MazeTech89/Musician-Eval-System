"""Storage helpers for performance audio files."""

import shutil
from pathlib import Path
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import UploadFile

from app.core.config import settings


class S3StorageError(Exception):
    """Raised when S3 storage operations fail."""


def is_s3_configured() -> bool:
    """Return whether minimum S3 configuration is present."""
    return bool(settings.s3_bucket_name and settings.aws_region)


def is_local_upload_storage_enabled() -> bool:
    """Return whether uploads should be written to local disk."""
    return settings.use_local_upload_storage or not is_s3_configured()


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


def _build_object_key(collection: str, owner_id: int, filename: str) -> str:
    suffix = Path(filename).suffix.lower() or ".bin"
    return f"{collection}/{owner_id}/{uuid4().hex}{suffix}"


def _build_local_upload_path(collection: str, owner_id: int, filename: str) -> Path:
    suffix = Path(filename).suffix.lower() or ".bin"
    upload_root = Path(settings.local_upload_dir)
    return upload_root / collection / str(owner_id) / f"{uuid4().hex}{suffix}"


def _save_audio_locally(audio_file: UploadFile, owner_id: int, collection: str) -> str:
    """Persist an uploaded audio file on local disk and return a public path."""
    target_path = _build_local_upload_path(collection=collection, owner_id=owner_id, filename=audio_file.filename or "")
    target_path.parent.mkdir(parents=True, exist_ok=True)

    audio_file.file.seek(0)
    with target_path.open("wb") as target_file:
        shutil.copyfileobj(audio_file.file, target_file)

    return f"/uploads/{collection}/{owner_id}/{target_path.name}"


def upload_audio_to_s3(audio_file: UploadFile, owner_id: int, collection: str) -> str:
    """Upload an audio file to S3 or local storage and return its location."""
    if is_local_upload_storage_enabled():
        return _save_audio_locally(audio_file=audio_file, owner_id=owner_id, collection=collection)

    if not is_s3_configured():
        raise S3StorageError("S3 upload is not configured. Set AWS_REGION and S3_BUCKET_NAME.")

    if not settings.s3_bucket_name:
        raise S3StorageError("S3 bucket is not configured.")

    object_key = _build_object_key(collection=collection, owner_id=owner_id, filename=audio_file.filename or "")
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


def upload_performance_audio_to_s3(audio_file: UploadFile, musician_id: int) -> str:
    """Upload a performance audio file to S3 and return an S3 URI."""
    return upload_audio_to_s3(audio_file=audio_file, owner_id=musician_id, collection="performances")
