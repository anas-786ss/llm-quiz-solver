import requests
import os
import json

API = os.getenv("API_URL", "http://127.0.0.1:8000/quiz")
SECRET = os.getenv("SECRET", "mysecret123")

payload = {
    "email": "test@example.com",
    "secret": SECRET,
    "url": "https://tds-llm-analysis.s-anand.net/demo"
}

print("Posting demo payload to", API)
resp = requests.post(API, json=payload)
print("Status:", resp.status_code)
try:
    print("Response:", json.dumps(resp.json(), indent=2))
except Exception:
    print("Response text:", resp.text)
