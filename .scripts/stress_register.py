#!/usr/bin/env python3
"""
Stress test script: POSTs multiple unique registration payloads to the API.
Usage: python .scripts/stress_register.py --count 100 --delay 0.05
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
import uuid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000/api/v1/auth/register")
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--delay", type=float, default=0.05)
    parser.add_argument("--base", default="stress-musician")
    args = parser.parse_args()

    try:
        with open("payload.json") as f:
            base_payload = json.load(f)
    except Exception as e:
        print("ERR: failed to read payload.json:", e)
        sys.exit(2)

    failures = 0
    for i in range(args.count):
        unique = f"{args.base}-{int(time.time()*1000)}-{i}-{uuid.uuid4().hex[:6]}"
        payload = dict(base_payload)
        payload["username"] = unique
        payload["email"] = f"{unique}@example.com"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            args.url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                status = resp.getcode()
                body = resp.read().decode("utf-8", errors="replace")
            print(f"{i+1}/{args.count}: {status} - {payload['username']}")
            if status >= 500:
                print("SERVER 5xx BODY:")
                print(body)
                failures += 1
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print(f"{i+1}/{args.count}: HTTP {e.code} - {payload['username']}")
            print(body)
            if e.code >= 500:
                failures += 1
        except Exception as e:
            print(
                f"{i+1}/{args.count}: ERR exception for {payload['username']}: {repr(e)}"
            )
            failures += 1
        time.sleep(args.delay)

    print("Stress test complete. failures=", failures)
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
