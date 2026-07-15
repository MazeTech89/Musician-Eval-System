#!/usr/bin/env python3
"""Direct S3 upload test."""

import asyncio
import io

from app.services.s3_storage import S3StorageService
from fastapi import UploadFile


async def test_upload():
    """Test S3 upload directly."""
    service = S3StorageService()

    # Create a test file
    test_content = b"test audio content"
    test_file = UploadFile(
        file=io.BytesIO(test_content),
        size=len(test_content),
        filename="test.wav",
        content_type="audio/wav",
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
