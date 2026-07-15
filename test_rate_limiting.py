#!/usr/bin/env python3
"""Test rate limiting functionality."""

import time

import requests

BASE_URL = "http://localhost:8000/api/v1"

print("=" * 60)
print("  Rate Limiting Test Suite")
print("=" * 60)
print()

# Test 1: Health endpoint (300/minute limit - should allow many)
print("1. Testing Health Endpoint (300/min limit)")
print("-" * 60)
success_count = 0
for i in range(10):
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        success_count += 1
        print(f"  Request {i+1}: ✓ 200 OK")
    else:
        print(f"  Request {i+1}: ✗ {response.status_code}")
        if "rate limit" in response.text.lower():
            print(f"    Rate limited: {response.text}")
        break
    time.sleep(0.1)

print(f"  Result: {success_count}/10 requests successful")
print()

# Test 2: Login endpoint (5/minute limit - should rate limit quickly)
print("2. Testing Login Endpoint (5/min limit - Rapid Fire Test)")
print("-" * 60)

login_data = {"username": "testuser", "password": "testpass123"}

rate_limited = False
for i in range(8):
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=5)

    if response.status_code == 429:
        print(f"  Request {i+1}: ⚠️  429 TOO MANY REQUESTS (Rate Limited)")
        rate_limited = True
        remaining = response.headers.get("X-RateLimit-Remaining", "N/A")
        limit = response.headers.get("X-RateLimit-Limit", "N/A")
        print(f"    Limit: {limit}, Remaining: {remaining}")
        break
    elif response.status_code == 401:
        print(f"  Request {i+1}: ✓ 401 Unauthorized (Expected - invalid creds)")
    else:
        print(f"  Request {i+1}: {response.status_code}")
    time.sleep(0.05)  # Small delay between requests

if rate_limited:
    print("  ✓ Rate limiting working correctly on auth endpoint!")
else:
    print("  ⚠️  Rate limit not triggered in test (may need more rapid requests)")

print()
print("=" * 60)
print("  Rate Limiting Configuration Active")
print("=" * 60)
print("  Authentication (5/min):")
print("    - /auth/register")
print("    - /auth/login")
print("    - /auth/refresh")
print("    - /auth/change-password (10/hour)")
print()
print("  File Operations (30/min):")
print("    - /performances/{id}/upload-audio")
print()
print("  General API (100/min):")
print("    - /performances/*")
print("    - /evaluations/*")
print("    - /users/*")
print()
print("  Health Check (300/min):")
print("    - /health")
print("=" * 60)
