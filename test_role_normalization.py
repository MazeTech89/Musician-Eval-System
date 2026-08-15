#!/usr/bin/env python3
"""Test role normalization fix."""

import json
import sys
import time
from datetime import datetime

import requests

time.sleep(2)  # Wait for backend to fully restart

BASE_URL = "http://localhost:8000/api/v1"
TIMESTAMP = datetime.now().strftime("%Y%m%d%H%M%S")


def post_register_with_retry(payload: dict, retries: int = 3):
    """Retry registration briefly when auth rate limiting is hit."""
    for attempt in range(retries + 1):
        response = requests.post(f"{BASE_URL}/auth/register", json=payload, timeout=5)
        if response.status_code != 429:
            return response

        if attempt < retries:
            retry_after_header = response.headers.get("Retry-After")
            retry_after = int(retry_after_header) if retry_after_header else 25
            wait_seconds = max(retry_after, 25)
            print(
                f"⚠️  Rate limited on /auth/register; waiting {wait_seconds}s "
                "before retry..."
            )
            time.sleep(wait_seconds)

    return response


all_passed = True

# Test 1: Registration with uppercase role
print("Test 1: Registration with UPPERCASE role")
print("=" * 60)
test_data_upper = {
    "username": f"testuser_upper_{TIMESTAMP}",
    "email": f"testuser_upper_{TIMESTAMP}@example.com",
    "password": "SecurePassword123!",
    "first_name": "Test",
    "last_name": "User",
    "role": "MUSICIAN",  # uppercase
}

print(f"Sending: {json.dumps(test_data_upper, indent=2)}\n")

response = post_register_with_retry(test_data_upper)

print(f"Status: {response.status_code}")
if response.status_code in [201, 200]:
    data = response.json()
    print(f"✅ Success! User created with role: {data.get('role')}")
    print(f"Response: {json.dumps(data, indent=2)}")
else:
    print(f"❌ Failed: {response.json()}")
    all_passed = False

print("\n")

# Test 2: Registration with lowercase role
print("Test 2: Registration with lowercase role")
print("=" * 60)
test_data_lower = {
    "username": f"testuser_lower_{TIMESTAMP}",
    "email": f"testuser_lower_{TIMESTAMP}@example.com",
    "password": "SecurePassword123!",
    "first_name": "Test",
    "last_name": "User",
    "role": "musician",  # lowercase
}

print(f"Sending: {json.dumps(test_data_lower, indent=2)}\n")

response = post_register_with_retry(test_data_lower)

print(f"Status: {response.status_code}")
if response.status_code in [201, 200]:
    data = response.json()
    print(f"✅ Success! User created with role: {data.get('role')}")
    print(f"Response: {json.dumps(data, indent=2)}")
else:
    print(f"❌ Failed: {response.json()}")
    all_passed = False

print("\n")

# Test 3: Registration with mixed case role
print("Test 3: Registration with MIXED CASE role")
print("=" * 60)
test_data_mixed = {
    "username": f"testuser_mixed_{TIMESTAMP}",
    "email": f"testuser_mixed_{TIMESTAMP}@example.com",
    "password": "SecurePassword123!",
    "first_name": "Test",
    "last_name": "User",
    "role": "MusiciaN",  # mixed case
}

print(f"Sending: {json.dumps(test_data_mixed, indent=2)}\n")

response = post_register_with_retry(test_data_mixed)

print(f"Status: {response.status_code}")
if response.status_code in [201, 200]:
    data = response.json()
    print(f"✅ Success! User created with role: {data.get('role')}")
    print(f"Response: {json.dumps(data, indent=2)}")
else:
    print(f"❌ Failed: {response.json()}")
    all_passed = False

sys.exit(0 if all_passed else 1)
