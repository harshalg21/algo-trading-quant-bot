import os
import sys
import requests
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.execution.upstox_sync import UPSTOX_ACCESS_TOKEN

headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {UPSTOX_ACCESS_TOKEN}"
}

print("="*75)
print(" 🔍 UPSTOX API CONNECTION DIAGNOSTIC TOOL")
print("="*75)

# Fetch Public IP
try:
    ip = requests.get('https://api.ipify.org', timeout=5).text
    print(f"📍 Your Current Laptop Public IP : {ip}")
except Exception as e:
    print(f"IP Fetch error: {e}")

print("\n📡 Testing Upstox Endpoints...")

endpoints = [
    ("User Profile", "https://api.upstox.com/v2/user/profile"),
    ("Positions", "https://api.upstox.com/v2/portfolio/short-term-positions"),
    ("Holdings", "https://api.upstox.com/v2/portfolio/long-term-holdings"),
    ("Funds & Margin", "https://api.upstox.com/v2/user/get-funds-and-margin")
]

for name, url in endpoints:
    try:
        res = requests.get(url, headers=headers, timeout=5)
        print(f"\n• {name} ({res.status_code}):")
        if res.status_code == 200:
            print("  🟢 SUCCESS! Live data received from Upstox:")
            print("  " + json.dumps(res.json(), indent=2)[:300] + "...")
        else:
            data = res.json()
            err_msg = data.get("errors", [{}])[0].get("message", res.text)
            err_code = data.get("errors", [{}])[0].get("errorCode", "")
            print(f"  🔴 FAILED [{err_code}]: {err_msg}")
    except Exception as e:
        print(f"  🔴 Request Error: {e}")

print("\n" + "="*75)
