#!/usr/bin/env python3
"""Direct S3 upload test."""

import asyncio
import io
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import UploadFile
from starlette.datastructures import Headers

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

load_dotenv(ROOT_DIR / ".env.local")

from app.services.s3_storage import S3StorageService


async def test_upload():
    """Test S3 upload directly."""
    service = S3StorageService()

    # Ensure test bucket exists in local S3/MinIO.
    try:
        service.s3_client.head_bucket(Bucket=service.bucket_name)
    except Exception:
        service.s3_client.create_bucket(Bucket=service.bucket_name)

    # Create a test file
    test_content = b"test audio content"
    test_file = UploadFile(
        file=io.BytesIO(test_content),
        size=len(test_content),
        filename="test.wav",
        headers=Headers({"content-type": "audio/wav"}),
    )

    try:
        result = await service.upload_audio(test_file, performance_id=1)
        print("✓ Upload succeeded:", result)
        return True
    except Exception as e:
        print("✗ Upload failed:", str(e))
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_upload())
    exit(0 if success else 1)
