#!/usr/bin/env python3
"""
Local testing script for S3 file upload functionality.

Tests:
1. Database connectivity
2. MinIO S3 bucket creation
3. File upload endpoint
4. Signed URL generation
5. File metadata retrieval
"""

import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_AUDIO_FILE = "test_audio.wav"

# Use timestamp to make test user unique
TIMESTAMP = int(datetime.now().timestamp())
TEST_USER = {
    "username": f"testmusician_{TIMESTAMP}",
    "email": f"test_{TIMESTAMP}@example.com",
    "password": "TestPass123!",
    "first_name": "Test",
    "last_name": "Musician",
    "role": "musician",
}


def create_test_audio_file(
    filename: str = TEST_AUDIO_FILE, duration_ms: int = 100
) -> str:
    """Create a minimal WAV file for testing.

    Args:
        filename: Output filename
        duration_ms: Duration in milliseconds

    Returns:
        Path to created file
    """
    import struct
    import wave

    sample_rate = 44100
    num_samples = int(sample_rate * duration_ms / 1000)

    # Create WAV file with silence (all zeros)
    with wave.open(filename, "w") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        # Write silence
        silence = struct.pack("<h", 0) * num_samples
        wav_file.writeframes(silence)

    print(f"✓ Created test audio file: {filename}")
    return filename


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def test_api_health():
    """Test API health endpoint."""
    print_header("1. Testing API Health")

    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ API is healthy")
            print(f"  Response: {response.json()}")
            return True
        else:
            print(f"✗ API health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to API. Is it running?")
        print(f"  Make sure backend is running on {API_BASE_URL}")
        return False


def test_register_user():
    """Register a test user."""
    print_header("2. Registering Test User")

    try:
        response = None
        for attempt in range(4):
            response = requests.post(
                f"{API_BASE_URL}/auth/register", json=TEST_USER, timeout=5
            )
            if response.status_code != 429:
                break
            retry_after_header = response.headers.get("Retry-After")
            retry_after = int(retry_after_header) if retry_after_header else 20
            wait_seconds = max(retry_after, 20)
            print(
                f"⚠ Registration rate limited (attempt {attempt + 1}/4). "
                f"Waiting {wait_seconds}s..."
            )
            time.sleep(wait_seconds)

        if response is None:
            print("✗ Registration request did not complete")
            return None

        if response.status_code == 201:
            print("✓ User registered successfully")
            print(f"  User: {TEST_USER['username']}")
            return response.json()
        elif response.status_code == 409:
            print("⚠ User already exists")
            return {"username": TEST_USER["username"]}
        else:
            print(f"✗ Registration failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error during registration: {e}")
        return None


def test_login():
    """Login and get access token."""
    print_header("3. Logging In")

    try:
        response = None
        for attempt in range(4):
            response = requests.post(
                f"{API_BASE_URL}/auth/login",
                json={
                    "username": TEST_USER["username"],
                    "password": TEST_USER["password"],
                },
                timeout=5,
            )
            if response.status_code != 429:
                break
            retry_after_header = response.headers.get("Retry-After")
            retry_after = int(retry_after_header) if retry_after_header else 20
            wait_seconds = max(retry_after, 20)
            print(
                f"⚠ Login rate limited (attempt {attempt + 1}/4). "
                f"Waiting {wait_seconds}s..."
            )
            time.sleep(wait_seconds)

        if response is None:
            print("✗ Login request did not complete")
            return None

        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print("✓ Login successful")
            print(f"  Token: {token[:20]}...")
            return token
        else:
            print(f"✗ Login failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error during login: {e}")
        return None


def test_create_performance(token: str):
    """Create a performance record."""
    print_header("4. Creating Performance Record")

    headers = {"Authorization": f"Bearer {token}"}
    performance_data = {
        "title": "Test Performance",
        "description": "A test performance for file upload",
        "audio_file_url": None,
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/performances",
            json=performance_data,
            headers=headers,
            timeout=5,
        )
        if response.status_code == 201:
            data = response.json()
            performance_id = data.get("id")
            print("✓ Performance created successfully")
            print(f"  Performance ID: {performance_id}")
            print(f"  Title: {data.get('title')}")
            return performance_id
        else:
            print(f"✗ Performance creation failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error during performance creation: {e}")
        return None


def test_file_upload(token: str, performance_id: int, audio_file: str):
    """Test file upload endpoint."""
    print_header("5. Testing File Upload")

    headers = {"Authorization": f"Bearer {token}"}

    # Check if file exists
    if not Path(audio_file).exists():
        print(f"✗ Audio file not found: {audio_file}")
        return None

    try:
        with open(audio_file, "rb") as f:
            files = {"file": (audio_file, f, "audio/wav")}

            response = requests.post(
                f"{API_BASE_URL}/performances/{performance_id}/upload-audio",
                files=files,
                headers=headers,
                timeout=30,
            )

        if response.status_code == 200:
            data = response.json()
            print("✓ File uploaded successfully")
            print(f"  S3 Key: {data.get('s3_key')}")
            print(f"  File Size: {data.get('file_size')} bytes")
            print(f"  File URL: {data.get('file_url')}")
            return data
        else:
            print(f"✗ Upload failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error during file upload: {e}")
        return None


def test_get_performance(token: str, performance_id: int):
    """Get performance details."""
    print_header("6. Retrieving Performance Details")

    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(
            f"{API_BASE_URL}/performances/{performance_id}",
            headers=headers,
            timeout=5,
        )
        if response.status_code == 200:
            data = response.json()
            print("✓ Performance retrieved successfully")
            print(f"  Title: {data.get('title')}")
            print(f"  S3 Key: {data.get('audio_s3_key')}")
            print(f"  File Size: {data.get('file_size_bytes')} bytes")
            print(f"  Uploaded At: {data.get('uploaded_at')}")
            return data
        else:
            print(f"✗ Retrieval failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error retrieving performance: {e}")
        return None


def test_invalid_file_upload(token: str, performance_id: int):
    """Test invalid file upload (should fail)."""
    print_header("7. Testing Invalid File Upload (Expected to Fail)")

    headers = {"Authorization": f"Bearer {token}"}

    # Create an invalid file (not audio format)
    invalid_file = "test_invalid.txt"
    with open(invalid_file, "w") as f:
        f.write("This is not an audio file")

    try:
        with open(invalid_file, "rb") as f:
            files = {"file": (invalid_file, f, "text/plain")}

            response = requests.post(
                f"{API_BASE_URL}/performances/{performance_id}/upload-audio",
                files=files,
                headers=headers,
                timeout=5,
            )

        # This should fail
        if response.status_code >= 400:
            print("✓ Invalid file correctly rejected")
            print(f"  Status: {response.status_code}")
            print(f"  Error: {response.json().get('detail', response.text)}")
            return True
        else:
            print("✗ Invalid file was not rejected (unexpected)")
            return False
    except Exception as e:
        print(f"✗ Error during invalid upload test: {e}")
        return False
    finally:
        Path(invalid_file).unlink(missing_ok=True)


def test_large_file_upload(token: str, performance_id: int):
    """Test large file rejection."""
    print_header("8. Testing Large File Rejection (Expected to Fail)")

    headers = {"Authorization": f"Bearer {token}"}

    # Create a large file (> 50MB)
    large_file = "test_large.wav"
    file_size_mb = 100

    print(f"  Creating {file_size_mb}MB test file...")
    with open(large_file, "wb") as f:
        f.write(b"\x00" * (file_size_mb * 1024 * 1024))

    try:
        with open(large_file, "rb") as f:
            files = {"file": (large_file, f, "audio/wav")}

            response = requests.post(
                f"{API_BASE_URL}/performances/{performance_id}/upload-audio",
                files=files,
                headers=headers,
                timeout=30,
            )

        # This should fail
        if response.status_code >= 400:
            print("✓ Large file correctly rejected")
            print(f"  Status: {response.status_code}")
            print(f"  Error: {response.json().get('detail', response.text)}")
            return True
        else:
            print("✗ Large file was not rejected (unexpected)")
            return False
    except Exception as e:
        print(f"✗ Error during large file test: {e}")
        return False
    finally:
        Path(large_file).unlink(missing_ok=True)


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  Musician Evaluation System - Local Testing Suite")
    print("=" * 60)

    # Create test audio file
    audio_file = create_test_audio_file()

    # Run tests
    results = {}

    # 1. Health check
    results["health"] = test_api_health()
    if not results["health"]:
        print("\n✗ API is not running. Start with: docker compose up --build")
        return False

    time.sleep(1)

    # 2. Register user
    user_data = test_register_user()
    results["register"] = user_data is not None

    time.sleep(1)

    # 3. Login
    token = test_login()
    results["login"] = token is not None

    if not token:
        print("\n✗ Cannot proceed without token")
        return False

    time.sleep(1)

    # 4. Create performance
    performance_id = test_create_performance(token)
    results["performance_create"] = performance_id is not None

    if not performance_id:
        print("\n✗ Cannot proceed without performance ID")
        return False

    time.sleep(1)

    # 5. File upload
    upload_result = test_file_upload(token, performance_id, audio_file)
    results["file_upload"] = upload_result is not None

    time.sleep(1)

    # 6. Get performance
    perf_data = test_get_performance(token, performance_id)
    results["get_performance"] = perf_data is not None

    time.sleep(1)

    # 7. Invalid file upload
    results["invalid_upload"] = test_invalid_file_upload(token, performance_id)

    time.sleep(1)

    # 8. Large file upload
    results["large_file"] = test_large_file_upload(token, performance_id)

    # Summary
    print_header("Test Summary")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, passed_flag in results.items():
        status = "✓ PASS" if passed_flag else "✗ FAIL"
        print(f"  {status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    # Cleanup
    Path(audio_file).unlink(missing_ok=True)

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
