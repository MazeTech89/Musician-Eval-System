#!/usr/bin/env python3
"""Test role normalization fix."""

import json
import time

import requests

time.sleep(2)  # Wait for backend to fully restart

BASE_URL = "http://localhost:8000/api/v1"

# Test 1: Registration with uppercase role
print("Test 1: Registration with UPPERCASE role")
print("=" * 60)
test_data_upper = {
    "username": "testuser_upper",
    "email": "testuser_upper@example.com",
    "password": "SecurePassword123!",
    "first_name": "Test",
    "last_name": "User",
    "role": "MUSICIAN",  # uppercase
}

print(f"Sending: {json.dumps(test_data_upper, indent=2)}\n")

response = requests.post(f"{BASE_URL}/auth/register", json=test_data_upper, timeout=5)

print(f"Status: {response.status_code}")
if response.status_code in [201, 200]:
    data = response.json()
    print(f"✅ Success! User created with role: {data.get('role')}")
    print(f"Response: {json.dumps(data, indent=2)}")
else:
    print(f"❌ Failed: {response.json()}")

print("\n")

# Test 2: Registration with lowercase role
print("Test 2: Registration with lowercase role")
print("=" * 60)
test_data_lower = {
    "username": "testuser_lower",
    "email": "testuser_lower@example.com",
    "password": "SecurePassword123!",
    "first_name": "Test",
    "last_name": "User",
    "role": "musician",  # lowercase
}

print(f"Sending: {json.dumps(test_data_lower, indent=2)}\n")

response = requests.post(f"{BASE_URL}/auth/register", json=test_data_lower, timeout=5)

print(f"Status: {response.status_code}")
if response.status_code in [201, 200]:
    data = response.json()
    print(f"✅ Success! User created with role: {data.get('role')}")
    print(f"Response: {json.dumps(data, indent=2)}")
else:
    print(f"❌ Failed: {response.json()}")

print("\n")

# Test 3: Registration with mixed case role
print("Test 3: Registration with MIXED CASE role")
print("=" * 60)
test_data_mixed = {
    "username": "testuser_mixed",
    "email": "testuser_mixed@example.com",
    "password": "SecurePassword123!",
    "first_name": "Test",
    "last_name": "User",
    "role": "MusiciaN",  # mixed case
}

print(f"Sending: {json.dumps(test_data_mixed, indent=2)}\n")

response = requests.post(f"{BASE_URL}/auth/register", json=test_data_mixed, timeout=5)

print(f"Status: {response.status_code}")
if response.status_code in [201, 200]:
    data = response.json()
    print(f"✅ Success! User created with role: {data.get('role')}")
    print(f"Response: {json.dumps(data, indent=2)}")
else:
    print(f"❌ Failed: {response.json()}")
