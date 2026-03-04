import sys
import os

sys.path.append(r"e:\OrderSync\backend")

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# test a known static html file
response = client.get("/login/login.html")
print(f"Status Code: {response.status_code}")
print(f"Content-Type: {response.headers.get('content-type')}")

if "charset=utf-8" in str(response.headers.get("content-type")).lower():
    print("SUCCESS: charset=utf-8 is present in the headers.")
else:
    print("FAILED: charset=utf-8 is missing!")
