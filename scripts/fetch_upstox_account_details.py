import os
import sys
import json
import requests
from pathlib import Path

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.upstox_feed import UPSTOX_ACCESS_TOKEN

def fetch_all_upstox_account_details():
    print("="*75)
    print(" 🔍 FETCHING COMPLETE LIVE ACCOUNT & PORTFOLIO DETAILS FROM UPSTOX API")
    print("="*75)

    if not UPSTOX_ACCESS_TOKEN:
        print("❌ UPSTOX_ACCESS_TOKEN is missing in .env.")
        return

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {UPSTOX_ACCESS_TOKEN}"
    }

    endpoints = {
        "User Profile": "https://api.upstox.com/v2/user/profile",
        "Funds & Margin": "https://api.upstox.com/v2/user/get-funds-and-margin",
        "Positions": "https://api.upstox.com/v2/portfolio/short-term-positions",
        "Holdings": "https://api.upstox.com/v2/portfolio/long-term-holdings",
        "Order Book": "https://api.upstox.com/v2/order/retrieve-all",
        "GTT Rules": "https://api.upstox.com/v2/gtt/rules"
    }

    results = {}
    for name, url in endpoints.items():
        print(f"\nQuerying Upstox {name} API...")
        try:
            res = requests.get(url, headers=headers, timeout=10)
            print(f"Status Code: {res.status_code}")
            if res.status_code == 200:
                data = res.json()
                results[name] = data.get("data", {})
                print(f"✅ SUCCESS {name}: {json.dumps(results[name], indent=2)[:300]}...")
            else:
                print(f"⚠️ Response: {res.text}")
                results[name] = {"error": res.status_code, "msg": res.text}
        except Exception as e:
            print(f"❌ Error querying {name}: {e}")
            results[name] = {"error": str(e)}

    print("\n" + "="*75)
    print(" SUMMARY OF ACCOUNT FETCH ATTEMPT")
    print("="*75)
    return results

if __name__ == "__main__":
    fetch_all_upstox_account_details()
