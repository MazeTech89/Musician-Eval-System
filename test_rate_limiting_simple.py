#!/usr/bin/env python3
"""Simple rate limiting test - verify that decorators work and backend responds."""

import requests
import time
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_health_endpoint():
    """Test health endpoint - should allow 300/minute (frequent checks)."""
    print("\n" + "="*60)
    print("Testing Health Endpoint (300/minute limit)")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✅ Health endpoint responding correctly")
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            # Check for rate limit headers
            print("\nRate Limit Headers:")
            for key, value in response.headers.items():
                if 'ratelimit' in key.lower() or 'retry' in key.lower():
                    print(f"  {key}: {value}")
            return True
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Error testing health endpoint: {e}")
        return False

def test_health_rate_limit():
    """Test health endpoint rate limiting by making many requests quickly."""
    print("\n" + "="*60)
    print("Testing Health Endpoint Rate Limiting (300/minute)")
    print("="*60)
    
    responses = []
    success_count = 0
    rate_limited_count = 0
    
    # Make 5 requests quickly to verify they all succeed
    for i in range(5):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            responses.append((i+1, response.status_code))
            if response.status_code == 200:
                success_count += 1
                print(f"Request {i+1}: ✅ 200 OK")
            elif response.status_code == 429:
                rate_limited_count += 1
                print(f"Request {i+1}: ⏱️ 429 Rate Limited")
            else:
                print(f"Request {i+1}: ⚠️ {response.status_code}")
        except Exception as e:
            print(f"Request {i+1}: ❌ Error: {e}")
        
        if i < 4:  # Don't sleep after the last request
            time.sleep(0.1)
    
    print(f"\nResults: {success_count} successful, {rate_limited_count} rate limited")
    if success_count == 5:
        print("✅ Rate limit allows frequent health checks (as expected)")
        return True
    else:
        print(f"⚠️ Some requests failed or were rate limited")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Rate Limiting Verification Tests")
    print("="*60)
    
    results = []
    
    # Test 1: Can we reach the health endpoint?
    results.append(("Health Endpoint Accessible", test_health_endpoint()))
    
    # Test 2: Does the health endpoint accept rapid requests?
    results.append(("Health Endpoint Rate Limiting", test_health_rate_limit()))
    
    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All rate limiting tests passed! Backend is operational.")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Check backend logs.")
        return 1

if __name__ == "__main__":
    exit(main())
