import sys
import requests
import json
import gzip
from pathlib import Path

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.upstox_feed import UPSTOX_ACCESS_TOKEN

print("="*70)
print(" SEARCHING UPSTOX INSTRUMENT MASTER FOR EXACT MCX KEYS")
print("="*70)

# Download Upstox Complete Instrument Master File
url = "https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz"
try:
    res = requests.get(url, timeout=15)
    if res.status_code == 200:
        data_json = json.loads(gzip.decompress(res.content).decode('utf-8'))
        print(f"Downloaded {len(data_json)} instruments from Upstox Master.")

        mcx_matches = {}
        for item in data_json:
            trading_symbol = item.get("trading_symbol", "").upper()
            instrument_type = item.get("instrument_type", "").upper()
            if "FUT" in trading_symbol or instrument_type == "FUT":
                if any(k in trading_symbol for k in ["GOLDPETAL", "SILVERMIC", "CRUDEOILM", "NATGASMINI"]):
                    key = item.get("instrument_key")
                    name = item.get("name")
                    mcx_matches[trading_symbol] = key
                    print(f"✅ FOUND MCX FUTURES: '{trading_symbol}' -> instrument_key = '{key}'")
                    if len(mcx_matches) >= 15:
                        break
    else:
        print(f"Failed to download instrument master: Status {res.status_code}")
except Exception as e:
    print(f"Error fetching instrument master: {e}")
