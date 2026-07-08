#!/usr/bin/env python3
"""Check MinIO bucket contents."""

import boto3

s3 = boto3.client(
    "s3",
    endpoint_url="http://minio:9000",
    aws_access_key_id="minioadmin",
    aws_secret_access_key="minioadmin",
)

resp = s3.list_objects_v2(Bucket="development-musician-eval-uploads")

print('Files in MinIO bucket "development-musician-eval-uploads":')
if "Contents" in resp:
    for obj in resp["Contents"]:
        print(f"  - {obj['Key']} ({obj['Size']} bytes, uploaded {obj['LastModified']})")
else:
    print("  (bucket is empty)")
