"""S3 storage helpers for performance audio files."""

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
    """Upload a performance audio file to S3 and return an S3 URI."""
    if not is_s3_configured():
        raise S3StorageError(
            "S3 upload is not configured. Set AWS_REGION and S3_BUCKET_NAME."
        )

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
