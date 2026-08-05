import sys
from pathlib import Path

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.upstox_feed import UPSTOX_ACCESS_TOKEN, fetch_upstox_live_ohlc

def test_upstox_connection():
    print("="*60)
    print(" TESTING DIRECT UPSTOX API LIVE FEED")
    print("="*60)
    print(f"UPSTOX ACCESS TOKEN: {'CONFIGURED ✅' if UPSTOX_ACCESS_TOKEN else 'MISSING ❌'}")
    print("="*60)

    if not UPSTOX_ACCESS_TOKEN:
        print("\n❌ UPSTOX_ACCESS_TOKEN is missing in .env.")
        print("Steps to get your free token in 1 minute:")
        print("1. Log into Upstox Developer Console: https://api.upstox.com")
        print("2. Copy your Access Token and paste into .env: UPSTOX_ACCESS_TOKEN=\"your_token\"")
        return

    print("\nFetching 100% exact live quote from Upstox servers for SILVERMIC...")
    res = fetch_upstox_live_ohlc("MCX_FO|SILVERMIC31AUG26FUT")

    if res.get("status") == "SUCCESS":
        print("\n🎉 SUCCESS! Connected directly to Upstox Live Market Feed!")
        print(f"Live Quote Data: {res['ohlc']}")
    else:
        print(f"\n❌ Connection failed: {res.get('error')}")

if __name__ == "__main__":
    test_upstox_connection()
