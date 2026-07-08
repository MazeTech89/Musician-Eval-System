"""S3 storage service for audio file uploads and management."""

import logging
import os
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile

from app.core.config import settings

logger = logging.getLogger(__name__)


class S3StorageService:
    """Service for managing audio file uploads to AWS S3."""

    def __init__(self):
        """Initialize S3 client and bucket configuration."""
        self.s3_client = boto3.client("s3", **settings.get_s3_config())
        self.bucket_name = settings.s3_bucket_name_with_env
        self.allowed_formats = settings.s3_allowed_audio_formats
        self.max_file_size = settings.s3_max_file_size_mb * 1024 * 1024  # Convert to bytes

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
            file_ext = Path(file.filename).suffix.lower()
            s3_key = f"performances/{performance_id}/{file.filename}"

            # Read file content
            file_content = await file.read()

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
            # For local development with minio
            endpoint_url = os.getenv("S3_ENDPOINT_URL", f"s3.{settings.aws_region}.amazonaws.com")
            return f"https://{self.bucket_name}.{endpoint_url}/{s3_key}"
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
