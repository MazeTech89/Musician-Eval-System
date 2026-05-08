"""Pytest configuration and shared fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI application.

    Returns:
        TestClient: FastAPI test client
    """
    return TestClient(app)
