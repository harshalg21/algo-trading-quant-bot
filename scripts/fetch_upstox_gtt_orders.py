import os
import sys
import requests
import json
from pathlib import Path

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.execution.upstox_sync import UPSTOX_ACCESS_TOKEN

headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {UPSTOX_ACCESS_TOKEN}"
}

print("="*75)
print(" 🔄 FETCHING LIVE UPSTOX GTT RULES & HOLDINGS")
print("="*75)

endpoints = [
    ("GTT Rules", "https://api.upstox.com/v2/gtt/rules"),
    ("GTT Orders", "https://api.upstox.com/v2/gtt/orders"),
    ("Long Term Holdings", "https://api.upstox.com/v2/portfolio/long-term-holdings"),
    ("Short Term Positions", "https://api.upstox.com/v2/portfolio/short-term-positions"),
    ("Order Book", "https://api.upstox.com/v2/order/retrieve-all"),
    ("User Profile", "https://api.upstox.com/v2/user/profile")
]

for name, url in endpoints:
    print(f"\n--- {name} ({url}) ---")
    try:
        res = requests.get(url, headers=headers, timeout=10)
        print(f"HTTP Status: {res.status_code}")
        print(f"Response: {res.text[:400]}")
    except Exception as e:
        print(f"Error: {e}")

print("\n" + "="*75)
