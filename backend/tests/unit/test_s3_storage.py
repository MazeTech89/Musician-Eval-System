"""Tests for S3 storage URL generation."""

from app.services.s3_storage import S3StorageService, settings


def test_generate_file_url_normalizes_minio_endpoint(monkeypatch) -> None:
    service = object.__new__(S3StorageService)
    service.bucket_name = "development-musician-eval-uploads"

    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings, "s3_endpoint_url", "http://minio:9000")

    url = service._generate_file_url("performances/19/sample.mp3")

    assert (
        url == "http://localhost:9000/development-musician-eval-uploads/performances/19/sample.mp3"
    )


def test_generate_file_url_uses_localhost_endpoint(monkeypatch) -> None:
    service = object.__new__(S3StorageService)
    service.bucket_name = "development-musician-eval-uploads"

    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings, "s3_endpoint_url", "http://localhost:9000")

    url = service._generate_file_url("performances/19/sample.mp3")

    assert (
        url == "http://localhost:9000/development-musician-eval-uploads/performances/19/sample.mp3"
    )
