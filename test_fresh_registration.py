#!/usr/bin/env python3
"""Test fresh registration with new usernames."""

from datetime import datetime

import requests

BASE_URL = "http://localhost:8000/api/v1"

# Use timestamp to ensure unique usernames
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

# Test 1: Registration with uppercase role
print("Test 1: Registration with UPPERCASE role")
print("=" * 60)
test_data_upper = {
    "username": f"user_upper_{timestamp}",
    "email": f"upper_{timestamp}@example.com",
    "password": "SecurePassword123!",
    "first_name": "Test",
    "last_name": "Upper",
    "role": "MUSICIAN",  # uppercase
}

print(f"Username: {test_data_upper['username']}")
print(f"Role: {test_data_upper['role']}")

response = requests.post(f"{BASE_URL}/auth/register", json=test_data_upper, timeout=5)

print(f"Status: {response.status_code}")
if response.status_code in [201, 200]:
    data = response.json()
    print(f"✅ Success! User created with role: {data.get('role')}")
else:
    print(f"❌ Failed: {response.json()}")

print("\n")

# Test 2: Registration with evaluator role (uppercase)
print("Test 2: Registration with EVALUATOR role (uppercase)")
print("=" * 60)
test_data_eval = {
    "username": f"user_eval_{timestamp}",
    "email": f"eval_{timestamp}@example.com",
    "password": "SecurePassword456!",
    "first_name": "Test",
    "last_name": "Evaluator",
    "role": "EVALUATOR",  # uppercase
}

print(f"Username: {test_data_eval['username']}")
print(f"Role: {test_data_eval['role']}")

response = requests.post(f"{BASE_URL}/auth/register", json=test_data_eval, timeout=5)

print(f"Status: {response.status_code}")
if response.status_code in [201, 200]:
    data = response.json()
    print(f"✅ Success! User created with role: {data.get('role')}")
else:
    print(f"❌ Failed: {response.json()}")
