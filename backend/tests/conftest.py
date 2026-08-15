"""Pytest configuration and shared fixtures."""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Use an isolated SQLite database for tests to avoid external DB dependencies.
TEST_DB_PATH = Path(__file__).resolve().parent / "test.db"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{TEST_DB_PATH.as_posix()}")
os.environ.setdefault("ENVIRONMENT", "test")

from app.main import app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI application.

    Returns:
        TestClient: FastAPI test client
    """
    return TestClient(app)
