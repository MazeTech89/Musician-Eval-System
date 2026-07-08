#!/usr/bin/env python3
"""Test various registration payloads to identify 422 validation errors."""

import json
from datetime import datetime

import requests

BASE_URL = "http://localhost:8000/api/v1"
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")


def test_registration(description, data):
    """Test a registration request and display results."""
    print(f"\n{description}")
    print("=" * 60)
    print(f"Payload: {json.dumps(data, indent=2)}")

    response = requests.post(f"{BASE_URL}/auth/register", json=data, timeout=5)

    print(f"\nStatus: {response.status_code}")
    if response.status_code in [201, 200]:
        print("✅ Success!")
    else:
        print("Error Details:")
        print(json.dumps(response.json(), indent=2))

    return response.status_code


# Test 1: Missing password
print("\n" + "=" * 60)
print("VALIDATION ERROR TESTS")
print("=" * 60)

test_registration(
    "Test 1: Missing password field",
    {
        "username": f"user_{timestamp}_1",
        "email": f"test1_{timestamp}@example.com",
        "first_name": "Test",
        "last_name": "User",
        "role": "musician",
        # password is missing!
    },
)

# Test 2: Password too short
test_registration(
    "Test 2: Password too short (< 8 characters)",
    {
        "username": f"user_{timestamp}_2",
        "email": f"test2_{timestamp}@example.com",
        "password": "short",  # Less than 8 characters
        "first_name": "Test",
        "last_name": "User",
        "role": "musician",
    },
)

# Test 3: Invalid email format
test_registration(
    "Test 3: Invalid email format",
    {
        "username": f"user_{timestamp}_3",
        "email": "not-an-email",  # Invalid email
        "password": "ValidPassword123!",
        "first_name": "Test",
        "last_name": "User",
        "role": "musician",
    },
)

# Test 4: Missing username
test_registration(
    "Test 4: Missing username",
    {
        "email": f"test4_{timestamp}@example.com",
        "password": "ValidPassword123!",
        "first_name": "Test",
        "last_name": "User",
        "role": "musician",
        # username is missing!
    },
)

# Test 5: Username too short
test_registration(
    "Test 5: Username too short (< 3 characters)",
    {
        "username": "ab",  # Less than 3 characters
        "email": f"test5_{timestamp}@example.com",
        "password": "ValidPassword123!",
        "first_name": "Test",
        "last_name": "User",
        "role": "musician",
    },
)

# Test 6: Invalid role
test_registration(
    "Test 6: Invalid role value",
    {
        "username": f"user_{timestamp}_6",
        "email": f"test6_{timestamp}@example.com",
        "password": "ValidPassword123!",
        "first_name": "Test",
        "last_name": "User",
        "role": "invalid_role",  # Not a valid role
    },
)

# Test 7: Missing role
test_registration(
    "Test 7: Missing role",
    {
        "username": f"user_{timestamp}_7",
        "email": f"test7_{timestamp}@example.com",
        "password": "ValidPassword123!",
        "first_name": "Test",
        "last_name": "User",
        # role is missing!
    },
)

print("\n" + "=" * 60)
print("VALIDATION ERROR TESTS COMPLETE")
print("=" * 60)
