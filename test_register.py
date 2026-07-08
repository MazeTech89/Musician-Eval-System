#!/usr/bin/env python3
"""Test registration endpoint to see detailed 422 error."""

import json

import requests

BASE_URL = "http://localhost:8000/api/v1"

# Test with valid data
test_data = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePassword123!",
    "first_name": "Test",
    "last_name": "User",
    "role": "MUSICIAN",
}

print("Testing registration endpoint with:")
print(json.dumps(test_data, indent=2))
print("\n" + "=" * 60)

try:
    response = requests.post(f"{BASE_URL}/auth/register", json=test_data, timeout=5)

    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print("\nResponse Body:")
    print(json.dumps(response.json(), indent=2))

except Exception as e:
    print(f"Error: {e}")
