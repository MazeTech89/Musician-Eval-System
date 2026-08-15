"""S3 storage service for audio file uploads and management."""

import logging
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile

from app.core.config import settings

logger = logging.getLogger(__name__)


class S3StorageError(RuntimeError):
    """Raised when audio storage operations fail."""


class S3StorageService:
    """Service for managing audio file uploads to AWS S3."""

    def __init__(self):
        """Initialize S3 client and bucket configuration."""
        s3_config = settings.get_s3_config()
        logger.info(f"Initializing S3StorageService with config: {s3_config}")
        self.s3_client = boto3.client("s3", **s3_config)
        self.bucket_name = settings.s3_bucket_name_with_env
        self.allowed_formats = settings.s3_allowed_audio_formats
        self.max_file_size = settings.s3_max_file_size_mb * 1024 * 1024  # Convert to bytes
        logger.info(f"S3 bucket name: {self.bucket_name}")

    def _validate_file(self, file: UploadFile) -> tuple[bool, str]:
        """Validate uploaded file format and size.

        Args:
            file: Uploaded file

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file.filename:
            return False, "No filename provided"

        # Check file extension
        file_ext = Path(file.filename).suffix.lower().lstrip(".")
        if file_ext not in self.allowed_formats:
            return False, f"Invalid audio format. Allowed: {', '.join(self.allowed_formats)}"

        # Check file size
        if file.size and file.size > self.max_file_size:
            return False, f"File size exceeds maximum limit of {settings.s3_max_file_size_mb}MB"

        return True, ""

    async def upload_audio(self, file: UploadFile, performance_id: int) -> dict:
        """Upload audio file to S3.

        Args:
            file: Uploaded audio file
            performance_id: Associated performance ID

        Returns:
            Dictionary with s3_key and file_url

        Raises:
            ValueError: If file validation fails
            ClientError: If S3 upload fails
        """
        is_valid, error_msg = self._validate_file(file)
        if not is_valid:
            raise ValueError(error_msg)

        try:
            # Generate S3 key
            s3_key = f"performances/{performance_id}/{file.filename}"

            # Read file content
            file_content = await file.read()
            logger.info(
                "Uploading file to S3 - Bucket: %s, Key: %s, Size: %s bytes",
                self.bucket_name,
                s3_key,
                len(file_content),
            )

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=file.content_type or "audio/mpeg",
                Metadata={
                    "performance_id": str(performance_id),
                    "original_filename": file.filename,
                },
            )

            logger.info(f"Successfully uploaded audio file to S3: s3://{self.bucket_name}/{s3_key}")

            return {
                "s3_key": s3_key,
                "file_url": self._generate_file_url(s3_key),
                "file_size": len(file_content),
            }

        except ClientError as e:
            logger.error(f"S3 upload failed for performance {performance_id}: {e}")
            raise

    def _generate_file_url(self, s3_key: str) -> str:
        """Generate file URL for S3 object.

        For local S3-compatible (minio), returns local URL.
        For AWS S3, returns standard S3 URL.

        Args:
            s3_key: S3 object key

        Returns:
            File URL
        """
        if settings.environment == "development":
            # For local development with MinIO or other S3-compatible endpoints.
            endpoint_url = os.getenv("S3_ENDPOINT_URL", "")
            if endpoint_url:
                parsed = urlparse(
                    endpoint_url if "://" in endpoint_url else f"http://{endpoint_url}"
                )
                host = parsed.hostname or "localhost"
                if host == "minio":
                    host = "localhost"
                port = f":{parsed.port}" if parsed.port else ""
                base_path = parsed.path.rstrip("/")
                return f"{parsed.scheme or 'http'}://{host}{port}{base_path}/{self.bucket_name}/{s3_key}"

            return f"http://localhost:9000/{self.bucket_name}/{s3_key}"
        else:
            # For AWS S3
            return f"https://{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com/{s3_key}"

    def get_signed_url(self, s3_key: str, expiry_seconds: int | None = None) -> str:
        """Generate a signed URL for temporary access to S3 object.

        Args:
            s3_key: S3 object key
            expiry_seconds: URL expiry time in seconds (default from settings)

        Returns:
            Signed URL for downloading the file

        Raises:
            ClientError: If URL generation fails
        """
        expiry_seconds = expiry_seconds or settings.s3_signed_url_expiry_seconds

        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": s3_key},
                ExpiresIn=expiry_seconds,
            )
            logger.info(f"Generated signed URL for S3 key: {s3_key}")
            return url
        except ClientError as e:
            logger.error(f"Failed to generate signed URL for {s3_key}: {e}")
            raise

    def delete_file(self, s3_key: str) -> bool:
        """Delete file from S3.

        Args:
            s3_key: S3 object key

        Returns:
            True if deletion was successful

        Raises:
            ClientError: If deletion fails
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"Successfully deleted S3 object: {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete S3 object {s3_key}: {e}")
            raise

    def copy_file(self, source_key: str, destination_key: str) -> dict:
        """Copy file within S3.

        Args:
            source_key: Source S3 object key
            destination_key: Destination S3 object key

        Returns:
            Dictionary with copy metadata

        Raises:
            ClientError: If copy fails
        """
        try:
            copy_source = {"Bucket": self.bucket_name, "Key": source_key}
            self.s3_client.copy_object(
                CopySource=copy_source, Bucket=self.bucket_name, Key=destination_key
            )
            logger.info(f"Successfully copied S3 object from {source_key} to {destination_key}")
            return {"source_key": source_key, "destination_key": destination_key}
        except ClientError as e:
            logger.error(f"Failed to copy S3 object: {e}")
            raise

    def get_file_metadata(self, s3_key: str) -> dict:
        """Get metadata about S3 object.

        Args:
            s3_key: S3 object key

        Returns:
            Dictionary with file metadata

        Raises:
            ClientError: If metadata retrieval fails
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return {
                "key": s3_key,
                "size": response.get("ContentLength"),
                "content_type": response.get("ContentType"),
                "last_modified": response.get("LastModified"),
                "etag": response.get("ETag"),
                "metadata": response.get("Metadata", {}),
            }
        except ClientError as e:
            logger.error(f"Failed to get metadata for {s3_key}: {e}")
            raise

    def list_performance_files(self, performance_id: int) -> list[dict]:
        """List all files for a performance in S3.

        Args:
            performance_id: Performance ID

        Returns:
            List of file metadata dictionaries

        Raises:
            ClientError: If listing fails
        """
        try:
            prefix = f"performances/{performance_id}/"
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)

            files = []
            if "Contents" in response:
                for obj in response["Contents"]:
                    files.append(
                        {
                            "key": obj["Key"],
                            "size": obj["Size"],
                            "last_modified": obj["LastModified"],
                        }
                    )

            logger.info(f"Listed {len(files)} files for performance {performance_id}")
            return files
        except ClientError as e:
            logger.error(f"Failed to list files for performance {performance_id}: {e}")
            raise

    def create_bucket_if_not_exists(self) -> bool:
        """Create S3 bucket if it doesn't exist.

        Returns:
            True if bucket was created or already exists

        Raises:
            ClientError: If bucket creation fails
        """
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3 bucket '{self.bucket_name}' already exists")
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                try:
                    if settings.aws_region == "us-east-1":
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={"LocationConstraint": settings.aws_region},
                        )
                    logger.info(f"Created S3 bucket: {self.bucket_name}")
                    return True
                except ClientError as create_err:
                    logger.error(f"Failed to create S3 bucket: {create_err}")
                    raise
            else:
                raise

    def enable_cors(self) -> bool:
        """Enable CORS on S3 bucket.

        Returns:
            True if CORS configuration was successful

        Raises:
            ClientError: If CORS configuration fails
        """
        try:
            cors_config = {
                "CORSRules": [
                    {
                        "AllowedMethods": ["GET", "POST", "PUT"],
                        "AllowedOrigins": settings.cors_origins,
                        "AllowedHeaders": ["*"],
                        "ExposeHeaders": ["ETag"],
                        "MaxAgeSeconds": 3000,
                    }
                ]
            }
            self.s3_client.put_bucket_cors(Bucket=self.bucket_name, CORSConfiguration=cors_config)
            logger.info(f"Enabled CORS on S3 bucket: {self.bucket_name}")
            return True
        except ClientError as e:
            logger.error(f"Failed to enable CORS on S3 bucket: {e}")
            raise


# Singleton instance
_s3_service: S3StorageService | None = None


def get_s3_service() -> S3StorageService:
    """Get or create S3 storage service instance.

    Returns:
        S3StorageService instance
    """
    global _s3_service
    if _s3_service is None:
        _s3_service = S3StorageService()
    return _s3_service


def _resolve_local_upload_dir() -> Path:
    upload_dir = Path(getattr(settings, "local_upload_dir", "uploads"))
    if not upload_dir.is_absolute():
        upload_dir = Path.cwd() / upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def _extract_s3_key_from_url(audio_file_url: str) -> str:
    if audio_file_url.startswith("s3://"):
        without_scheme = audio_file_url[len("s3://") :]
        parts = without_scheme.split("/", 1)
        if len(parts) < 2 or not parts[1]:
            raise ValueError("Invalid S3 URL without object key")
        return parts[1]

    parsed = urlparse(audio_file_url)
    if not parsed.path:
        raise ValueError("Audio file URL does not contain a path")
    path_parts = parsed.path.lstrip("/").split("/", 1)
    if len(path_parts) < 2 or not path_parts[1]:
        raise ValueError("Audio file URL does not include an object key")
    return path_parts[1]


def upload_performance_audio_to_s3(audio_file: UploadFile, musician_id: int) -> str:
    """Upload a performance audio file and return its URL.

    Uses local storage when configured; otherwise attempts S3 and can optionally
    fall back to local storage when S3 is unavailable.
    """
    suffix = Path(audio_file.filename or "upload.wav").suffix or ".wav"
    unique_name = (
        f"{musician_id}_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}_{uuid4().hex}{suffix}"
    )

    if getattr(settings, "use_local_upload_storage", False):
        try:
            upload_dir = _resolve_local_upload_dir()
            output_path = upload_dir / unique_name
            audio_file.file.seek(0)
            output_path.write_bytes(audio_file.file.read())
            return f"/uploads/{output_path.name}"
        except Exception as exc:  # noqa: BLE001
            raise S3StorageError(f"Local upload failed: {exc}") from exc

    try:
        service = get_s3_service()
        audio_file.file.seek(0)
        file_content = audio_file.file.read()
        s3_key = f"performances/{musician_id}/{unique_name}"
        service.s3_client.put_object(
            Bucket=service.bucket_name,
            Key=s3_key,
            Body=file_content,
            ContentType=audio_file.content_type or "audio/mpeg",
        )
        return service._generate_file_url(s3_key)
    except Exception as exc:  # noqa: BLE001
        if getattr(settings, "s3_fallback_to_local", True):
            try:
                upload_dir = _resolve_local_upload_dir()
                output_path = upload_dir / unique_name
                audio_file.file.seek(0)
                output_path.write_bytes(audio_file.file.read())
                return f"/uploads/{output_path.name}"
            except Exception as fallback_exc:  # noqa: BLE001
                raise S3StorageError(
                    f"S3 upload and local fallback failed: {fallback_exc}"
                ) from fallback_exc
        raise S3StorageError(f"S3 upload failed: {exc}") from exc


def materialize_audio_file(audio_file_url: str) -> tuple[Path, bool]:
    """Resolve an audio URL to a local path.

    Returns tuple[path, is_temporary].
    """
    if not audio_file_url:
        raise ValueError("Audio file URL is missing")

    if audio_file_url.startswith("/uploads/"):
        upload_dir = _resolve_local_upload_dir()
        return upload_dir / Path(audio_file_url).name, False

    local_candidate = Path(audio_file_url)
    if local_candidate.exists():
        return local_candidate, False

    if audio_file_url.startswith("s3://") or audio_file_url.startswith("http"):
        try:
            s3_key = _extract_s3_key_from_url(audio_file_url)
            service = get_s3_service()
            suffix = Path(s3_key).suffix or ".wav"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                service.s3_client.download_fileobj(service.bucket_name, s3_key, tmp_file)
                return Path(tmp_file.name), True
        except Exception as exc:  # noqa: BLE001
            raise S3StorageError(f"Failed to materialize audio file: {exc}") from exc

    raise ValueError(f"Unsupported audio file URL format: {audio_file_url}")


def delete_audio_file(audio_file_url: str | None) -> None:
    """Delete an audio file from local storage or S3.

    This function is intentionally best-effort for delete flows.
    """
    if not audio_file_url:
        return

    try:
        if audio_file_url.startswith("/uploads/"):
            upload_dir = _resolve_local_upload_dir()
            (upload_dir / Path(audio_file_url).name).unlink(missing_ok=True)
            return

        local_candidate = Path(audio_file_url)
        if local_candidate.exists():
            local_candidate.unlink(missing_ok=True)
            return

        if audio_file_url.startswith("s3://") or audio_file_url.startswith("http"):
            s3_key = _extract_s3_key_from_url(audio_file_url)
            get_s3_service().delete_file(s3_key)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Best-effort delete failed for %s: %s", audio_file_url, exc)


def get_storage_health() -> dict[str, str | bool]:
    """Return simple health information for the configured storage backend."""
    if getattr(settings, "use_local_upload_storage", False):
        try:
            _resolve_local_upload_dir()
            return {"backend": "local", "healthy": True, "detail": "local upload directory ready"}
        except Exception as exc:  # noqa: BLE001
            return {"backend": "local", "healthy": False, "detail": str(exc)}

    try:
        service = get_s3_service()
        service.s3_client.head_bucket(Bucket=service.bucket_name)
        return {
            "backend": "s3",
            "healthy": True,
            "detail": f"bucket {service.bucket_name} reachable",
        }
    except Exception as exc:  # noqa: BLE001
        return {"backend": "s3", "healthy": False, "detail": str(exc)}
