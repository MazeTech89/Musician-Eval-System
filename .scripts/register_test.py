import json
import sys
import urllib.error
import urllib.request

url = "http://localhost:8000/api/v1/auth/register"
try:
    with open("payload.json") as f:
        payload = json.load(f)
except Exception as e:
    print("ERR: failed to read payload.json:", e)
    sys.exit(2)

data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(
    url, data=data, headers={"Content-Type": "application/json"}, method="POST"
)
try:
    print("SENDING request to", url)
    sys.stdout.flush()
    with urllib.request.urlopen(req, timeout=30) as resp:
        status = resp.getcode()
        headers = resp.getheaders()
        body = resp.read().decode("utf-8", errors="replace")
    print("STATUS:", status)
    print("HEADERS:")
    for k, v in headers:
        print(f"{k}: {v}")
    print("\nBODY:")
    print(body)
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", errors="replace")
    print("STATUS:", e.code)
    print("HEADERS:")
    for k, v in e.headers.items():
        print(f"{k}: {v}")
    print("\nBODY:")
    print(body)
except Exception as e:
    print("ERR: request exception:", repr(e))
    sys.exit(3)
