import sys
import requests
from pathlib import Path

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

print("="*60)
print(" TESTING DIRECT LIVE MCX MARKET DATA FEED")
print("="*60)

# Upstox Public Instrument Master Search for SILVERMIC
try:
    url = "https://api.upstox.com/v2/market-quote/ohlc?symbol=MCX_FO:SILVERMIC31AUG26FUT&interval=1d"
    res = requests.get(url, headers={"Accept": "application/json"}, timeout=10)
    print(f"Upstox API Response Status: {res.status_code}")
    print(res.text[:300])
except Exception as e:
        print(f"Upstox fetch error: {e}")
