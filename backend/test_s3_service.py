#!/usr/bin/env python3
"""Direct test of S3StorageService."""

import asyncio
import io
from fastapi import UploadFile

from app.services.s3_storage import get_s3_service


async def main():
    """Test S3StorageService."""
    service = get_s3_service()
    print(f"Service bucket: {service.bucket_name}")
    
    # Try to list buckets using the service's client
    try:
        buckets = service.s3_client.list_buckets()
        print(f"✓ Successfully listed {len(buckets['Buckets'])} bucket(s)")
        print(f"  Buckets: {[b['Name'] for b in buckets['Buckets']]}")
    except Exception as e:
        print(f"✗ Error listing buckets: {e}")
        return
    
    # Try to upload a test file
    test_file = UploadFile(
        file=io.BytesIO(b"test content"),
        size=12,
        filename="test_service.wav",
        content_type="audio/wav"
    )
    try:
        result = await service.upload_audio(test_file, 999)
        print(f"✓ Upload succeeded: {result}")
    except Exception as e:
        print(f"✗ Upload failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
