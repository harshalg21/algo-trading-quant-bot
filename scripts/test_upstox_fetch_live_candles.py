import sys
import json
import requests
import pandas as pd
from pathlib import Path

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.upstox_feed import UPSTOX_ACCESS_TOKEN

def test_fetch():
    print("="*70)
    print(" FETCHING LIVE MCX CANDLES DIRECTLY FROM UPSTOX SERVERS")
    print("="*70)

    keys = {
        "SILVERMIC 31AUG26 FUT": "MCX_FO|488788"
    }

    # First search Upstox master for current GOLDPETAL AUG contract key
    url_master = "https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz"
    res_m = requests.get(url_master, timeout=15)
    if res_m.status_code == 200:
        import gzip
        data = json.loads(gzip.decompress(res_m.content).decode('utf-8'))
        for item in data:
            ts = item.get("trading_symbol", "").upper()
            if "GOLDPETAL" in ts and "AUG" in ts and "FUT" in ts and item.get("segment") == "MCX_FO":
                keys["GOLDPETAL 31AUG26 FUT"] = item.get("instrument_key")
                print(f"Found Gold Petal Key: '{ts}' -> {item.get('instrument_key')}")
                break

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {UPSTOX_ACCESS_TOKEN}"
    }

    for name, key in keys.items():
        print(f"\nFetching live candles for '{name}' ({key})...")
        url = f"https://api.upstox.com/v2/historical-candle/{key}/day/2026-08-03/2026-04-01"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            print(f"Upstox API Status: {res.status_code}")
            data = res.json()
            candles = data.get("data", {}).get("candles", [])
            if candles:
                latest = candles[0]  # Latest candle
                print(f"✅ REAL UPSTOX PRICE FOR '{name}':")
                print(f"   • Open  : ₹{latest[1]:,.2f}")
                print(f"   • High  : ₹{latest[2]:,.2f}")
                print(f"   • Low   : ₹{latest[3]:,.2f}")
                print(f"   • Close : ₹{latest[4]:,.2f}")
            else:
                print(f"Response: {data}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_fetch()
